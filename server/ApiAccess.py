#!/usr/bin/env python3
import json
import os
import binascii
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import time
import uuid
import hashlib
from bson import json_util
import redis
import UnlockStaleTokens
from LDcommon import connectMongoDBReadOnly,getEmail,get_config

# blocked users attribute: 0=false, 1=true

config = get_config()
RUNTIME_BLOCK_REASON = "runtime_limit"
RUNTIME_BLOCK_COOLDOWN_MINUTES = int(config.get("runtime_block_cooldown_minutes", 120))

# ---------------------------------------------------------------------------
# Redis connection and runtime-counter helpers
# ---------------------------------------------------------------------------
RUNTIME_WINDOW_MS = 86400 * 1000  # 24-hour rolling window in milliseconds

_redis_client = None
_redis_checked = False
_redis_last_failure = None
REDIS_RETRY_INTERVAL = 60  # seconds between connection retries after failure


def get_redis_client():
    """Lazy-initialize a Redis client.  Returns None when disabled or unreachable."""
    global _redis_client, _redis_checked, _redis_last_failure
    if _redis_checked:
        return _redis_client
    # If the last attempt failed recently, skip retry to avoid per-request 2s timeouts
    if _redis_last_failure is not None and (time.time() - _redis_last_failure) < REDIS_RETRY_INTERVAL:
        return None
    _redis_checked = True

if os.environ.get("ENABLE_REDIS_CACHE", "NO").upper() != "YES":
    print("[Redis] Cache disabled via ENABLE_REDIS_CACHE")
    return None

    try:
        use_tls = os.environ.get("REDIS_TLS", "YES").upper() == "YES"
        client = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            db=int(os.environ.get("REDIS_DB", "0")),
            password=os.environ.get("REDIS_PASSWORD", None),
            ssl=use_tls,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        print("[Redis] Connected successfully")
        _redis_client = client
        return _redis_client
    except Exception as e:
        _redis_checked = False  # allow retry after cooldown
        _redis_last_failure = time.time()
        print(f"[Redis] Connection failed, falling back to MongoDB only: {e}")
        return None


def _runtime_cache_key(token):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"runtime:{token_hash}"


def incr_runtime_cache(token, duration_ms):
    """Add duration_ms to the rolling 24h runtime counter for token.

    Uses a Redis sorted set where each entry's score is the request's Unix
    timestamp in milliseconds.  A Lua script atomically:
      1. Adds the new entry  (score=now_ms, member="{duration_ms}:{uuid}").
      2. Evicts entries that fell outside the 24h rolling window.
      3. Returns the updated rolling total.

    This matches the MongoDB aggregation's ``accessed >= now - 24h`` semantics
    so the Redis fast path and the MongoDB fallback are always consistent.
    """
    r = get_redis_client()
    if r is None or duration_ms is None:
        return None
    try:
        key = _runtime_cache_key(token)
        now_ms = int(time.time() * 1000)
        # Member encodes duration first so Lua can parse it without ambiguity:
        # format is "{duration_ms}:{uuid_hex}" — take everything before the
        # first colon as the integer duration.
        member = f"{int(duration_ms)}:{uuid.uuid4().hex}"
        lua_script = """
            local key    = KEYS[1]
            local now_ms = tonumber(ARGV[1])
            local win_ms = tonumber(ARGV[2])
            local member = ARGV[3]

            -- Add this request's entry.
            redis.call('ZADD', key, now_ms, member)

            -- Evict entries older than the rolling window.
            redis.call('ZREMRANGEBYSCORE', key, '-inf',
                       '(' .. tostring(now_ms - win_ms))

            -- Sum durations of all surviving entries.
            local entries = redis.call('ZRANGE', key, 0, -1)
            local total = 0
            for _, m in ipairs(entries) do
                local colon = string.find(m, ':')
                total = total + tonumber(string.sub(m, 1, colon - 1))
            end

            -- Refresh TTL so the key lives exactly one more window.
            redis.call('EXPIRE', key, math.ceil(win_ms / 1000))
            return total
        """
        new_total = r.eval(lua_script, 1, key, now_ms, RUNTIME_WINDOW_MS, member)
        return new_total
    except Exception as e:
        print(f"[Redis] incr_runtime_cache error: {e}")
        return None


def get_runtime_cache(token):
    """Return the rolling 24h runtime total from Redis.

    Returns (True, total_ms) on cache hit, or (False, 0) when the sorted-set
    key is absent (cache miss — caller should fall back to MongoDB).
    Evicts stale entries atomically so the returned value is always current.
    """
    r = get_redis_client()
    if r is None:
        return (False, 0)
    try:
        key = _runtime_cache_key(token)
        now_ms = int(time.time() * 1000)
        lua_script = """
            local key    = KEYS[1]
            local now_ms = tonumber(ARGV[1])
            local win_ms = tonumber(ARGV[2])

            if redis.call('EXISTS', key) == 0 then
                return -1  -- sentinel: cache miss
            end

            -- Evict entries that have aged out of the rolling window.
            redis.call('ZREMRANGEBYSCORE', key, '-inf',
                       '(' .. tostring(now_ms - win_ms))

            -- Sum durations of all surviving entries.
            local entries = redis.call('ZRANGE', key, 0, -1)
            local total = 0
            for _, m in ipairs(entries) do
                local colon = string.find(m, ':')
                total = total + tonumber(string.sub(m, 1, colon - 1))
            end
            return total
        """
        result = r.eval(lua_script, 1, key, now_ms, RUNTIME_WINDOW_MS)
        if result == -1:
            return (False, 0)
        return (True, int(result))
    except Exception as e:
        print(f"[Redis] get_runtime_cache error: {e}")
        return (False, 0)


def clear_runtime_cache(token):
    """Delete cached runtime counter (called on unblock / budget reset)."""
    r = get_redis_client()
    if r is None:
        return
    try:
        r.delete(_runtime_cache_key(token))
    except Exception as e:
        print(f"[Redis] clear_runtime_cache error: {e}")


def _parse_datetime(value):
    if isinstance(value, datetime.datetime):
        if value.tzinfo is not None:
            return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return value
    if isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.datetime.fromisoformat(normalized)
            if parsed.tzinfo is not None:
                return parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return parsed
        except ValueError:
            return None
    return None

# connect to email account
def smtp_connect(email_account):
    smtp = smtplib.SMTP(email_account)
    smtp.set_debuglevel(1)
    return smtp

# send email
def smtp_send(smtp, email_account, email, packet):
    # retries twice upon failure (often connection timeout)
    try:
        smtp_debug = smtp.sendmail("NCILDlinkWebAdmin@mail.nih.gov", email, packet.as_string())
        print(smtp_debug)
        smtp.quit()
    except Exception:
        smtp.quit()
        smtp = smtp_connect(email_account)
        try:
            smtp_send(smtp, email_account, email, packet)
        except Exception:
            smtp.quit()
            smtp = smtp_connect(email_account)
            smtp_send(smtp, email_account, email, packet)

# email user token
def emailUser(email, token, expiration, firstname, token_expiration, email_account, url_root):
    print("sending message registered")
    new_url_root = url_root.replace('http://', 'https://')
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    message = ''
    if token_expiration:
        message = 'Dear ' + firstname + ', ' + '<br><br>' + 'Thank you for registering to use the LDlink API! <br><br>' + 'Your token is: ' + token + '<br>' + 'Your token expires on: ' + expiration + '<br><br>' + 'Please include this token as part of the submitted argument in your LDlink API requests. Examples of how to use a LDlink token are described in the <a href="'+ new_url_root + '"><u>API Access</u></a> tab. Please do not share this token with other users as misuse of this token will result in potential blocking or termination of API use. <br><br>Thanks again for your interest in LDlink,<br><br>' + 'LDlink Web Admin'
    else:
        message = 'Dear ' + firstname + ', ' + '<br><br>' + 'Thank you for registering to use the LDlink API! <br><br>' + 'Your token is: ' + token + '<br><br>' + 'Please include this token as part of the submitted argument in your LDlink API requests. Examples of how to use a LDlink token are described in the <a href="' + new_url_root + '"><u>API Access</u></a> tab. Please do not share this token with other users as misuse of this token will result in potential blocking or termination of API use. <br><br>Thanks again for your interest in LDlink,<br><br>' + 'LDlink Web Admin'
    #print(MIMEText(message, 'html'))
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, email, packet)

# email user when their token is blocked
def emailUserBlocked(email, email_account, url_root):
    print("sending message blocked")
    new_url_root = url_root.replace('http://', 'https://')
    if ("https" not in new_url_root):
        new_url_root = "https://"+new_url_root
    #print(new_url_root)
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token Blocked"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    message = "Dear " + str(email) + ", " + "<br><br>"
    message += "Your LDlink API access token has been blocked.<br><br>"
    message += "To unblock, resubmit a request in LDlink's <a href=\"" + new_url_root + "/?tab=apiaccess\"><u>API Access</u></a> tab with the same email address.<br><br>"
    message += "Please contact the LDlink Web Admin (NCILDlinkWebAdmin@mail.nih.gov) for any questions or concerns.<br><br>"
    message += "LDlink Web Admin"
    print(MIMEText(message, 'html'))
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, email, packet)

# email user when their token is unblocked
def emailUserUnblocked(email, email_account):
    print("sending message unblocked")
    packet = MIMEMultipart()
    packet['Subject'] = "LDLink API Access Token Unblocked"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    packet['To'] = email
    
    message = "Dear " + str(email) + ", " + "<br><br>"
    message += "Your LDlink API access token has been unblocked.<br><br>"
    message += "Please contact the LDlink Web Admin (NCILDlinkWebAdmin@mail.nih.gov) for any questions or concerns.<br><br>"
    message += "LDlink Web Admin"
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, email, packet)

# email unblock request to list of web admins
def emailJustification(firstname, lastname, email, institution, registered, blocked, justification, url_root):
    email_account = config["email_smtp_host"]
    api_superuser = config["email_superuser"]
    api_superuser_token = getToken(api_superuser)
    print("sending message justification")
    new_url_root = url_root.replace('http://', 'https://').replace('?tab=apiaccess','')
    if ("https" not in new_url_root):
        new_url_root = "https://"+new_url_root
    bool_blocked = ""
    if blocked == "1":
        bool_blocked = "True"
    else:
        bool_blocked = "False"
    # emailList = approval_email_list.split(', ') # change to NCILDlinkWebAdmin email or a list of emails later
    packet = MIMEMultipart()
    packet['Subject'] = "[Unblock Request] LDLink API Access User"
    packet['From'] = "NCI LDlink Web Admin" + " <NCILDlinkWebAdmin@mail.nih.gov>"
    # packet['To'] = ", ".join(emailList)
    packet['To'] = api_superuser
    message = "The following user has submitted an unblock request:"
    message += "<br><br>First name: " + str(firstname)
    message += "<br>Last name: " + str(lastname)
    message += "<br>Email: " + str(email)
    message += "<br>Registered: " + str(registered)
    message += "<br>Blocked: " + str(bool_blocked)
    message += "<br><br>Justification: " + str(justification)
    message += "<br><br>Please review user details and justification. To unblock the user, click the link below."
    message += '<br><br><u><a href="' + str(new_url_root) + '/LDlinkRestWeb/apiaccess/unblock_user?email=' + str(email) + '&token=' + str(api_superuser_token) + '">Click here to unblock user.</a></u>'
    #print(MIMEText(message, 'html'))
    packet.attach(MIMEText(message, 'html'))
    smtp = smtp_connect(email_account)
    smtp_send(smtp, email_account, api_superuser, packet)
    out_json = {
        "email": email,
        "justification": justification
    }
    return out_json

# check if user email record exists
def getEmailRecord(email):
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    emailRecord = users.find_one({"email": email})
    return emailRecord

def insertUser(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr):
    db = connectMongoDBReadOnly(False,True)
    user = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "institution": institution,
        "token": token,
        "registered": registered,
        "blocked": blocked,
        "locked": 0
    }
    users = db.api_users
    users.insert_one(user).inserted_id

# log token's api call to api_log table
def logAccess(token, module, duration_ms=None):
    db = connectMongoDBReadOnly(False,True,True)
    accessed = getDatetime()
    
    log = {
        "token": token,
        "module": module,
        "accessed": accessed
    }
    if duration_ms is not None:
        log["duration_ms"] = int(duration_ms)
        if token not in (None, "NA"):
            incr_runtime_cache(token, int(duration_ms))
    logs = db.api_log
    logs.insert_one(log).inserted_id


# sum token runtime from api_log over a rolling 24-hour window
def getTokenRuntimeLast24Hours(token):
    # Fast path: read from Redis counter
    is_cached, cached_total_ms = get_runtime_cache(token)
    if is_cached:
        print(f"[getTokenRuntimeLast24Hours] Redis cache hit: total_ms={cached_total_ms}")
        return cached_total_ms

    # Slow path: MongoDB aggregation (cache miss or Redis unavailable)
    db = connectMongoDBReadOnly(False,True,True)
    logs = db.api_log
    users = db.api_users
    window_start = getDatetime() - datetime.timedelta(hours=24)
    effective_window_start = window_start

    user_record = users.find_one({"token": token}, {"runtime_budget_reset_at": 1})
    runtime_budget_reset_at = None
    if user_record is not None:
        runtime_budget_reset_at = _parse_datetime(user_record.get("runtime_budget_reset_at"))
        if runtime_budget_reset_at is not None and runtime_budget_reset_at > effective_window_start:
            effective_window_start = runtime_budget_reset_at

    pipeline = [
        {
            "$match": {
                "token": token,
                "accessed": {"$gte": effective_window_start},
                "duration_ms": {"$exists": True}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_duration_ms": {"$sum": "$duration_ms"}
            }
        }
    ]

    result = list(logs.aggregate(pipeline))
    total_ms = 0
    if len(result) == 0:
        total_ms = 0
    else:
        total_ms = int(result[0].get("total_duration_ms", 0))

    # Do not seed Redis from the aggregated MongoDB total.  A synthetic entry
    # scored at now_ms would keep usage from requests spread across the past
    # 24h alive for another full window, over-counting and potentially
    # blocking tokens prematurely.  Instead, let the cache warm organically:
    # incr_runtime_cache() adds real per-request entries after each completed
    # call, and once the key exists those entries correctly represent the
    # rolling window.  Until then, this MongoDB path is the authoritative
    # source and handles the budget check correctly.

    print(
        f"[getTokenRuntimeLast24Hours] MongoDB fallback: window_start={window_start} effective_window_start={effective_window_start} "
        f"runtime_budget_reset_at={runtime_budget_reset_at} total_ms={total_ms}"
    )
    return total_ms

# sets blocked attribute of user to 1=true
def blockUser(email, url_root):
    email_account = getEmail()
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been blocked. An email has been sent to the user."
    }
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    update_operation = users.find_one_and_update(
        {"email": email},
        {"$set": {"blocked": 1, "blocked_reason": "admin_manual", "blocked_at": getDatetime(), "blocked_until": None}}
    )
    if update_operation is None:
        return None
    emailUserBlocked(email, email_account, url_root)
    return out_json


# sets blocked attribute of token owner to 1=true
def blockToken(token, url_root):
    email_account = getEmail()
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    record = users.find_one({"token": token})

    if record is None:
        print(f"[blockToken] Token not found in api_users: {token}")
        return None

    email = record.get("email")
    if int(record.get("blocked", 0)) == 1:
        print(f"[blockToken] Token already blocked: {token} (email={email})")
        return {
            "message": "Token is already blocked."
        }

    blocked_at = getDatetime()
    blocked_until = blocked_at + datetime.timedelta(minutes=RUNTIME_BLOCK_COOLDOWN_MINUTES)
    update_result = users.find_one_and_update(
        {"token": token},
        {"$set": {
            "blocked": 1,
            "blocked_reason": RUNTIME_BLOCK_REASON,
            "blocked_at": blocked_at,
            "blocked_until": blocked_until,
        }}
    )
    print(f"[blockToken] Updated token to blocked: email={email} update_result={update_result is not None}")

    if email:
        try:
            emailUserBlocked(email, email_account, url_root)
            print(f"[blockToken] Sent blocked email to: {email}")
        except Exception as e:
            print(f"[blockToken] Failed to send email to {email}: {e}")

    return {
        "message": "Token has been blocked due to runtime limit policy."
    }

# sets blocked attribute of user to 0=false
def unblockUser(email):
    email_account = getEmail()
    out_json = {
        "message": "Email user (" + email + ")'s API token access has been unblocked. An email has been sent to the user."
    }
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    record = users.find_one({"email": email})
    if record is None:
        return None
    token = record.get("token")
    update_operation = users.find_one_and_update(
        {"email": email},
        {"$set": {
            "blocked": 0,
            "blocked_reason": None,
            "blocked_at": None,
            "blocked_until": None,
            "runtime_budget_reset_at": getDatetime(),
        }}
    )
    if update_operation is None:
        return None
    if token:
        clear_runtime_cache(token)
    emailUserUnblocked(email, email_account)
    return out_json

# sets locked attribute of user to lockValue
def setUserLock(email, lockValue):
    out_json = {
        "message": "Email user (" + email + ")'s lock has been set to " + str(lockValue)
    }
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    update_operation = users.find_one_and_update({"email": email}, { "$set": {"locked": int(lockValue)}})
    if update_operation is None:
        return None
    return out_json


# sets api2auth attribute of user to authValue
def setUserApi2Auth(email, authValue):
    out_json = {
        "message": "Email user (" + email + ")'s api2auth has been set to " + str(authValue)
    }
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    locked = 0
    if int(authValue) == 1:
        locked = -1
    update_operation = users.find_one_and_update({"email": email}, { "$set": {"api2auth": int(authValue),"locked":locked}})
    if update_operation is None:
        return None
    return out_json

# sets locked attribute of all users to 0=false
def unlockAllUsers():
    UnlockStaleTokens.main()
    
    out_json = {
        "message": "All tokens have been unlocked."
    }
    return out_json

# update record only if email's token is expired and user re-registers
def updateRecord(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr):
    db = connectMongoDBReadOnly(False,True)
    user = {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "institution": institution,
        "token": token,
        "registered": registered,
        "blocked": blocked
    }
    users = db.api_users
    users.find_one_and_update({"email": email}, { "$set": user})

# check if token is valid when hitting API route and not expired
def checkToken(token, token_expiration, token_expiration_days):
    db = connectMongoDBReadOnly(False,True,True)
    users = db.api_users
    record = users.find_one({"token": token})

    if record is None:
        return False
    else:
        # return True
        present = getDatetime()
        # registered = datetime.datetime.strptime(record["registered"], "%Y-%m-%d %H:%M:%S")
        registered = record["registered"]
        expiration = getExpiration(registered, token_expiration_days)
        if ((present < expiration) or not token_expiration):
            return True
        else:
            return False

# check if token is authorized to access API server 2
def checkApiServer2Auth(token):
    db = connectMongoDBReadOnly(False,True,True)
    users = db.api_users
    record = users.find_one({"token": token})

    if record is None:
        return False
    else:
        if "api2auth" in record and record["api2auth"] == 1:
            return True
        else:
            return False

# given email, return token
def getToken(email):
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    record = users.find_one({"email": email})
    if record is None:
        return None
    else:
        return record["token"]

# check if token is blocked (1=blocked, 0=not blocked). returns (is_blocked, reason) tuple
# is_blocked: True if token is currently blocked, False otherwise
# reason: 'runtime_limit' or other reason string if blocked, None if not blocked
def checkBlocked(token):
    db = connectMongoDBReadOnly(False,True,True)
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return (False, None)
    else:
        if int(record.get("blocked", 0)) != 1:
            return (False, None)

        blocked_reason = record.get("blocked_reason", "unknown")

        # Only runtime-limit blocks auto-expire. Other block reasons stay blocked.
        if blocked_reason == RUNTIME_BLOCK_REASON:
            now = getDatetime()
            blocked_until = record.get("blocked_until")

            if blocked_until is None:
                blocked_at = record.get("blocked_at")
                if blocked_at is not None:
                    blocked_at = _parse_datetime(blocked_at)
                    if blocked_at is not None:
                        blocked_until = blocked_at + datetime.timedelta(minutes=RUNTIME_BLOCK_COOLDOWN_MINUTES)

            if blocked_until is not None:
                blocked_until = _parse_datetime(blocked_until)
                if blocked_until is not None and now >= blocked_until:
                    users.find_one_and_update(
                        {"token": token},
                        {
                            "$set": {
                                "blocked": 0,
                                "blocked_reason": None,
                                "blocked_at": None,
                                "blocked_until": None,
                                "runtime_budget_reset_at": now,
                            }
                        }
                    )
                    print(f"[checkBlocked] Auto-unblocked runtime-limited token after cooldown")
                    clear_runtime_cache(token)
                    return (False, None)

        return (True, blocked_reason)

# check if token is locked (1=locked, 0=not locked, -1=never locked). returns true (1) if token is locked
def checkLocked(token):
    db = connectMongoDBReadOnly(False,True,True)
    users = db.api_users
    record = users.find_one({"token": token})

    if record is None:
        return False
    else:
        if "locked" in record:
            if record["locked"] == 0 or record["locked"] == -1:
                return False
            else:
                return True
        else:
            return False

def toggleLocked(token, lock):
    if config['restrict_concurrency']:
        db = connectMongoDBReadOnly(False,True,True)
        users = db.api_users
        record = users.find_one({"token": token})

        # bypass lock toggle if user has -1 locked flag set (unlimited api calls)
        if record["locked"] != -1:
            if lock == 1:
                calcStartTime = getDatetime()
                users.find_one_and_update({"token": token}, { "$set": {"locked": calcStartTime}})
            else: 
                users.find_one_and_update({"token": token}, { "$set": {"locked": lock}})

# check if email is blocked (1=blocked, 0=not blocked). returns true if email is blocked
def checkBlockedEmail(email):
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    record = users.find_one({"email": email})
    print(record)
    if record is None:
        return False
    else:
        if int(record["blocked"]) == 1:
            return True
        else:
            return False

# check if token is already in db
def checkUniqueToken(token):
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    record = users.find_one({"token": token})
    if record is None:
        return False
    else:
        return True

# generate unique access token for each user
def generateToken():
    token = binascii.b2a_hex(os.urandom(6)).decode('utf-8')
    # if true, generate another token - make sure example token is not generated
    while(checkUniqueToken(token) or token == "faketoken123"):
        token = binascii.b2a_hex(os.urandom(6)).decode('utf-8')
    return token

# get current date and time
def getDatetime():
    return datetime.datetime.now()

# get current date and time
def getExpiration(registered, token_expiration_days):
    return registered + datetime.timedelta(days=token_expiration_days)

# registers new users and emails generated token for WEB
def register_user(firstname, lastname, email, institution, reference, url_root):
    # with open('config.yml', 'r') as yml_file:
    #     config = yaml.load(yml_file)
    env = config['env']
    api_mongo_addr = config['mongodb_host']
    token_expiration = config['token_expiration']
    token_expiration_days = config['token_expiration_days']
    email_account = config["email_smtp_host"]
    out_json = {}
    # by default, users are not blocked
    blocked = 0
    record = getEmailRecord(email)
    # print record
    # if email record exists, do not insert to db
    if record != None:
        if checkBlockedEmail(record["email"]):
            registered = record["registered"]
            format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
            out_json = {
                "message": "Your email is associated with a blocked API token.",
                "firstname": record["firstname"],
                "lastname": record["lastname"],
                "email": record["email"],
                "institution": record["institution"],
                "token": record["token"],
                "registered": format_registered,
                "blocked": record["blocked"]
            }
        else:
            present = getDatetime()
            # registered = datetime.datetime.strptime(record["registered"], "%Y-%m-%d %H:%M:%S")
            registered = record["registered"]
            expiration = getExpiration(registered, token_expiration_days)
            format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
            format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
            if ((present < expiration) or not token_expiration):
                out_json = {
                    "message": "Email already registered.",
                    "firstname": record["firstname"],
                    "lastname": record["lastname"],
                    "email": record["email"],
                    "institution": record["institution"],
                    "token": record["token"],
                    "registered": format_registered,
                    "blocked": record["blocked"]
                }
                emailUser(record["email"], record["token"], format_expiration, record["firstname"], token_expiration, email_account, url_root)
            else:
                token = generateToken()
                registered = getDatetime()
                expiration = getExpiration(registered, token_expiration_days)
                format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
                format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
                updateRecord(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr)
                out_json = {
                    "message": "Thank you for registering to use the LDlink API.",
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": email,
                    "institution": institution,
                    "token": token,
                    "registered": format_registered,
                    "blocked": blocked
                }
                emailUser(email, token, format_expiration, firstname, token_expiration, email_account, url_root)
    else:
        # if email record does not exists in db, add to table
        token = generateToken()
        registered = getDatetime()
        expiration = getExpiration(registered, token_expiration_days)
        format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        format_expiration = expiration.strftime("%Y-%m-%d %H:%M:%S")
        insertUser(firstname, lastname, email, institution, token, registered, blocked, env, api_mongo_addr)
        out_json = {
            "message": "Thank you for registering to use the LDlink API.",
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "institution": institution,
            "token": token,
            "registered": format_registered,
            "blocked": blocked
        }
        emailUser(email, token, format_expiration, firstname, token_expiration, email_account, url_root)
    return out_json

# returns stats of total number of calls per registered api users with optional arguments
# optional arguments: startdatetime of api calls, enddatetime of api calls, top # users with most calls
def getStats(startdatetime, enddatetime, top):
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    log = db.api_log
    # get number of registered users in total
    numUsers = users.count()
    # join api_log and api_users by foreign key to retrieve user info per api_log record
    pipeline = [
        { 
            "$lookup" : { 
                "from" : "api_users", 
                "localField" : "token", 
                "foreignField" : "token", 
                "as" : "user_info" 
            } 
        }, 
        {   
            '$unwind' : "$user_info" 
        },
        {   
            "$project" : {
                "accessed" : 1,
                "module" : 1,
                "userinfo" : {
                    "email" : "$user_info.email",
                    "firstname" : "$user_info.firstname",
                    "lastname" : "$user_info.lastname"
                }
            } 
        },
        { 
            "$group": { 
                "_id": "$userinfo", 
                "#_api_calls": { 
                    "$sum": 1 
                } 
            } 
        }, 
        { 
            "$sort": { 
                "#_api_calls": -1 
            } 
        }
    ]
    # handle if top parameter is indicated or not
    if top is not False:
        pipeline.append({ "$limit": int(top) })
    # handle startdatetime and enddatetime parameters
    if ((startdatetime is not False) or (enddatetime is not False)):
        rangeQuery = {}
        if ((startdatetime is not False) and (enddatetime is False)):
            fromdatetime = startdatetime.split("-")
            if (len(fromdatetime) == 6): 
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), int(fromdatetime[5]), 0)
            elif (len(fromdatetime) == 3):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), 0, 0, 0, 0)
            elif (len(fromdatetime) == 5):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), 0, 0)
            else:
                return { "message": "Invalid input parameters."}
            rangeQuery = { "$match": { "accessed": { "$gte": from_datetime } } }
        if ((enddatetime is not False) and (startdatetime is False)):
            todatetime = enddatetime.split("-")
            if (len(fromdatetime) == 6): 
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), int(todatetime[5]), 0)
            elif (len(fromdatetime) == 3):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), 23, 59, 59, 0)
            elif (len(fromdatetime) == 5):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), 59, 0)
            else:
                return { "message": "Invalid input parameters."}
            rangeQuery = { "$match": { "accessed": { "$lt": to_datetime } } }
        if ((startdatetime is not False) and (enddatetime is not False)):
            fromdatetime = startdatetime.split("-")
            if (len(fromdatetime) == 6): 
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), int(fromdatetime[5]), 0)
            elif (len(fromdatetime) == 3):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), 0, 0, 0, 0)
            elif (len(fromdatetime) == 5):
                from_datetime = datetime.datetime(int(fromdatetime[0]), int(fromdatetime[1]), int(fromdatetime[2]), int(fromdatetime[3]), int(fromdatetime[4]), 0, 0)
            else:
                return { "message": "Invalid input parameters."}
            todatetime = enddatetime.split("-")
            if (len(todatetime) == 6): 
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), int(todatetime[5]), 0)
            elif (len(todatetime) == 3):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), 23, 59, 59, 0)
            elif (len(todatetime) == 5):
                to_datetime = datetime.datetime(int(todatetime[0]), int(todatetime[1]), int(todatetime[2]), int(todatetime[3]), int(todatetime[4]), 59, 0)
            else:
                return { "message": "Invalid input parameters."}
            rangeQuery = { "$match": { "accessed": { "$gte": from_datetime, "$lt": to_datetime } } }
        pipeline.insert(3, rangeQuery)
    users_json = log.aggregate(pipeline)
    # santize string to be returned as proper json
    users_json_sanitized = json.loads(json_util.dumps(users_json))
    numCalls = 0
    for user in users_json_sanitized:
        numCalls += int(user['#_api_calls'])
    out_json = {
        "#_total_registered_users": numUsers,
        "#_total_api_calls": numCalls,
        "users": users_json_sanitized
    }
    return out_json

# returns stats of api users with locked tokens
def getLockedUsers():
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    locked_users_json = users.find({"locked": {"$exists": True, "$ne": 0}},  { "firstname": 1, "lastname": 1, "email": 1, "locked": 1,  "_id": 0 })
    locked_users_json_sanitized = json.loads(json_util.dumps(locked_users_json))
    numLockedUsers = len(locked_users_json_sanitized)
    out_json = {
        "#_locked_users": numLockedUsers,
        "locked_users": locked_users_json_sanitized
    }
    return out_json

# returns stats of api users with blocked tokens
def getBlockedUsers():
    db = connectMongoDBReadOnly(False,True)
    users = db.api_users
    blocked_users_json = users.find({"blocked": {"$exists": True, "$ne": 0}},  { "firstname": 1, "lastname": 1, "email": 1, "blocked": 1,  "_id": 0 })
    blocked_users_json_sanitized = json.loads(json_util.dumps(blocked_users_json))
    numBlockedUsers = len(blocked_users_json_sanitized)
    out_json = {
        "#_blocked_users": numBlockedUsers,
        "blocked_users": blocked_users_json_sanitized
    }
    return out_json

def lookupUser(email):
    user_record = getEmailRecord(email)

    if user_record != None:
        registered = user_record["registered"]
        format_registered = registered.strftime("%Y-%m-%d %H:%M:%S")
        locked = user_record["locked"]

        try:
            format_locked = locked.strftime("%Y-%m-%d %H:%M:%S")
        except:
            format_locked = locked
            
        out_json = {
            "email": user_record["email"],
            "firstname": user_record["firstname"],
            "lastname": user_record["lastname"],
            "institution": user_record["institution"],
            "token": user_record["token"],
            "registered": format_registered,
            "blocked": user_record["blocked"],
            "locked": format_locked,
            "admin":user_record["admin"] if "admin" in user_record else "NA",
            "api2auth":user_record["api2auth"] if "api2auth" in user_record else "NA"
        }
    else:
        out_json = "No record found"
    return out_json

