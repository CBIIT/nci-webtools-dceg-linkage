"use client";
import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { Container, Row, Col, Alert, Spinner } from "react-bootstrap";

// Helper functions for parsing and rendering results (copied from form.tsx, can be improved)
function parseHeritabilityResult(result: string) {
  // Split by lines and parse each line by the first colon
  const lines = result.split(/\r?\n/).filter(l => l.trim() && !/^[-]+$/.test(l));
  const parsed: Record<string, string> = {};
  let lastKey = '';
  lines.forEach(line => {
    const idx = line.indexOf(':');
    if (idx !== -1) {
      const key = line.slice(0, idx).trim();
      const value = line.slice(idx + 1).trim();
      parsed[key] = value;
      lastKey = key;
    } else if (lastKey) {
      // If the line contains 'Ratio' (with or without <, >, =), treat it as a new Ratio row
      const ratioMatch = line.match(/(Ratio\s*[<>=]?.*)/i);
      if (ratioMatch) {
        parsed['Ratio'] = ratioMatch[1].replace(/^Ratio\s*/i, '').trim();
        lastKey = 'Ratio';
      } else {
        parsed[lastKey] += ' ' + line.trim();
      }
    }
  });
  return {
    h2: parsed['Total Observed scale h2'] || '',
    lambdaGC: parsed['Lambda GC'] || '',
    meanChi2: parsed['Mean Chi^2'] || '',
    intercept: parsed['Intercept'] || '',
    ratio: parsed['Ratio'] || '',
  };
}

function parseGeneticCorrelationResult(resultStr: string) {
  const startIdx = resultStr.search(/Heritability of phenotype 1/i);
  if (startIdx === -1) return {};
  const trimmed = resultStr.slice(startIdx);
  const headers = [
    'Heritability of phenotype 1',
    'Heritability of phenotype 2/2',
    'Genetic Covariance',
    'Genetic Correlation',
    'Summary of Genetic Correlation Results',
  ];
  const indices = headers.map(h => {
    const re = new RegExp(`^${h}`, 'im');
    const m = trimmed.match(re);
    return m ? trimmed.indexOf(m[0]) : -1;
  });
  const sections: Record<string, string> = {};
  for (let i = 0; i < headers.length; ++i) {
    if (indices[i] === -1) continue;
    const start = indices[i] + headers[i].length;
    const end = indices.slice(i + 1).find(idx => idx > indices[i]) ?? trimmed.length;
    sections[headers[i]] = trimmed.slice(start, end).trim();
  }
  return {
    herit1: sections['Heritability of phenotype 1'] || '',
    herit2: sections['Heritability of phenotype 2/2'] || '',
    gencov: sections['Genetic Covariance'] || '',
    gencorr: sections['Genetic Correlation'] || '',
    summary: sections['Summary of Genetic Correlation Results'] || '',
  };
}

function TableContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="table-responsive" style={{ maxWidth: 600, margin: '0 auto', overflowX: 'auto' }}>
      {children}
    </div>
  );
}

function renderKeyValueTable(section: string) {
  if (!section) return null;
  const lines = section.split(/\r?\n/).filter(l => l.trim() && !/^[-]+$/.test(l));
  const kvPairs: [string, string][] = [];
  lines.forEach(line => {
    let found = false;
    const colonPairs = line.matchAll(/([\w\s²\*\-]+?):\s*([^:<>]+?)(?=(?:[A-Z][^:]*:|$))/g);
    for (const pair of colonPairs) {
      kvPairs.push([pair[1].trim(), pair[2].trim()]);
      found = true;
    }
    if (!found) {
      const angleMatch = line.match(/([\w\s²\*\-]+?)([<>])\s*([^<>=]+)/);
      if (angleMatch) {
        kvPairs.push([angleMatch[1].trim(), angleMatch[2] + ' ' + angleMatch[3].trim()]);
        found = true;
      }
    }
    if (!found) {
      kvPairs.push(['', line.trim()]);
    }
  });
  return (
    <TableContainer>
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0, width: 'auto', tableLayout: 'auto', maxWidth: '100%' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}></th>
            <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>Value</th>
          </tr>
        </thead>
        <tbody>
          {kvPairs.map(([k, v], i) => (
            <tr key={i}>
              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{k}</td>
              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableContainer>
  );
}

function renderSummaryTable(section: string) {
  if (!section) return null;
  const lines = section.split(/\r?\n/).filter(l => l.trim());
  const endIdx = lines.findIndex(l => /^Analysis\s+finished\s+at/i.test(l));
  const filteredLines = endIdx === -1 ? lines : lines.slice(0, endIdx);
  let headerIdx = 0;
  while (headerIdx < filteredLines.length && filteredLines[headerIdx].split(/\s+/).length < 2) headerIdx++;
  if (headerIdx >= filteredLines.length - 1) return <pre>{section}</pre>;
  const header = filteredLines[headerIdx].split(/\s+/).filter(Boolean);
  const rows = filteredLines.slice(headerIdx + 1).map(l => l.split(/\s+/).filter(Boolean));
  return (
    <TableContainer>
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0, width: 'auto', tableLayout: 'auto', maxWidth: '100%' }}>
        <thead >
          <tr>{header.map((h, i) => <th key={i} style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((cols, i) => <tr key={i}>{cols.map((c, j) => <td key={j} style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{c}</td>)}</tr>)}
        </tbody>
      </table>
    </TableContainer>
  );
}

function HeritabilityResultTable({ result }: { result: string }) {
  const parsed = parseHeritabilityResult(result);
  const rows = [
    ['Total Observed scale h²', parsed.h2],
    ['Lambda GC', parsed.lambdaGC],
    ['Mean Chi²', parsed.meanChi2],
    ['Intercept', parsed.intercept],
    ['Ratio', parsed.ratio],
  ];
  return (
    <TableContainer>
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0,width: 'auto', tableLayout: 'auto', maxWidth: '100%' }}>
        <thead>
          <tr>
            <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>Metric</th>
            <th style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>Value</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(([k, v], i) => (
            <tr key={i}>
              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{k}</td>
              <td style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableContainer>
  );
}

function CollapsibleRawPanel({ result, title }: { result: string; title: string }) {
  const [showRaw, setShowRaw] = useState(false);
  return (
    <div className="panel panel-default mt-3" style={{ maxWidth: 600, margin: '20px auto 0 auto', border: '1px solid #bdbdbd', borderRadius: 6, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
      <div className="panel-heading" style={{ fontWeight: 600, background: '#f5f5f5', padding: '8px 12px', borderBottom: '1px solid #ddd', borderTopLeftRadius: 6, borderTopRightRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>{title}</span>
        <button
          type="button"
          className="btn btn-sm btn-outline-primary"
          onClick={() => setShowRaw((open) => !open)}
          aria-expanded={showRaw}
          aria-controls="heritRawPanelBody"
        >
          {showRaw ? "Collapse" : "Expand"}
        </button>
      </div>
      <div
        id="heritRawPanelBody"
        className={showRaw ? "panel-body" : "panel-body collapse"}
        style={{ padding: showRaw ? '12px' : 0, display: showRaw ? 'block' : 'none', background: '#f9f9f9' }}
      >
        <pre style={{ fontSize: '0.97em', whiteSpace: 'pre-wrap', margin: 0 }}>{result}</pre>
      </div>
    </div>
  );
}

// Helper to format heritability table as plain text
function formatHeritabilityTableText(result: string) {
  const parsed = parseHeritabilityResult(result);
  const rows = [
    ['Total Observed scale h²', parsed.h2],
    ['Lambda GC', parsed.lambdaGC],
    ['Mean Chi²', parsed.meanChi2],
    ['Intercept', parsed.intercept],
    ['Ratio', parsed.ratio],
  ];
  // Format as aligned text table
  const col1Width = Math.max(...rows.map(([k]) => k.length));
  const col2Width = Math.max(...rows.map(([,v]) => v.length));
  // Use tab instead of separator
  const header = ` \tValue`;
  const lines = [header, ...rows.map(([k, v]) => `${k}\t${v}`)];
  return lines.join('\n');
}

// Helper to format genetic correlation parsed tables as plain text
function formatGeneticCorrelationTableText(parsed: ReturnType<typeof parseGeneticCorrelationResult>) {
  let text = '';
  if (parsed.herit1) {
    text += 'Heritability of phenotype 1\n';
    text += formatKeyValueSection(parsed.herit1) + '\n\n';
  }
  if (parsed.herit2) {
    text += 'Heritability of phenotype 2\n';
    text += formatKeyValueSection(parsed.herit2) + '\n\n';
  }
  if (parsed.gencov) {
    text += 'Genetic Covariance\n';
    text += formatKeyValueSection(parsed.gencov) + '\n\n';
  }
  if (parsed.gencorr) {
    text += 'Genetic Correlation\n';
    text += formatKeyValueSection(parsed.gencorr) + '\n\n';
  }
  if (parsed.summary) {
    text += 'Summary of Genetic Correlation Results\n';
    text += formatSummarySection(parsed.summary) + '\n\n';
  }
  return text.trim();
}

function formatKeyValueSection(section: string) {
  const lines = section.split(/\r?\n/).filter(l => l.trim() && !/^[-]+$/.test(l));
  const kvPairs: [string, string][] = [];
  let lastKey = '';
  lines.forEach(line => {
    // If the line is a header like 'Heritability of phenotype 2/2', skip it
    if (/^Heritability of phenotype \d+(\/\d+)?$/.test(line.trim())) return;
    // If the line is just '/2' or similar, skip it
    if (/^\/\d+$/.test(line.trim())) return;
    // If the line is just a number (e.g. '2'), skip it
    if (/^\d+$/.test(line.trim())) return;
    const idx = line.indexOf(':');
    if (idx !== -1) {
      lastKey = line.slice(0, idx).trim();
      kvPairs.push([lastKey, line.slice(idx + 1).trim()]);
    } else if (lastKey) {
      // If the line contains 'Ratio' (with or without <, >, =), split it out as a new row
      const ratioMatch = line.match(/(Ratio\s*[<>=]?.*)/i);
      if (ratioMatch) {
        // If there is text before 'Ratio', append it to the previous value
        const before = line.slice(0, ratioMatch.index).trim();
        if (before) {
          const prev = kvPairs.pop();
          if (prev) kvPairs.push([prev[0], (prev[1] + ' ' + before).trim()]);
        }
        // Add Ratio as a new row
        kvPairs.push(['Ratio', ratioMatch[1].replace(/^Ratio\s*/i, '').trim()]);
        lastKey = 'Ratio';
      } else {
        // Remove leading whitespace from value
        const prev = kvPairs.pop();
        if (prev) {
          kvPairs.push([prev[0], (prev[1] + '\n' + line.trim()).replace(/^\s+/, '')]);
        }
      }
    } else {
      kvPairs.push(['', line.trim()]);
    }
  });
  if (!kvPairs.length) return '';
  // Use tab instead of separator
  const header = `\tValue`;
  const linesOut = [header, ...kvPairs.map(([k, v]) => `${k}\t${v}`)];
  return linesOut.join('\n');
}

function formatSummarySection(section: string) {
  const lines = section.split(/\r?\n/).filter(l => l.trim());
  const endIdx = lines.findIndex(l => /^Analysis\s+finished\s+at/i.test(l));
  const filteredLines = endIdx === -1 ? lines : lines.slice(0, endIdx);
  let headerIdx = 0;
  while (headerIdx < filteredLines.length && filteredLines[headerIdx].split(/\s+/).length < 2) headerIdx++;
  if (headerIdx >= filteredLines.length - 1) return section;
  const header = filteredLines[headerIdx].split(/\s+/).filter(Boolean);
  const rows = filteredLines.slice(headerIdx + 1).map(l => l.split(/\s+/).filter(Boolean));
  // Use tab instead of separator
  const headerLine = header.join('\t');
  const rowLines = rows.map(r => r.join('\t'));
  return [headerLine, ...rowLines].join('\n');
}

function DownloadOptionsPanel({ result, filename = "heritability_result.txt", inputFilename, parsedTableText }: { result: string; filename?: string; inputFilename?: string; parsedTableText?: string }) {
  const [zipping, setZipping] = useState(false);
  return (
    <div className="panel panel-default mt-3" style={{ maxWidth: 600, margin: '20px auto 0 auto', border: '1px solid #bdbdbd', borderRadius: 6, boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
      <div className="panel-heading" style={{ fontWeight: 600, background: '#f5f5f5', padding: '8px 12px', borderBottom: '1px solid #ddd', borderTopLeftRadius: 6, borderTopRightRadius: 6 }}>
        Download Options
      </div>
      <div className="panel-body" style={{ padding: '12px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
          {inputFilename && ((filename.includes('correlation') && inputFilename.split(',').length > 1) || (filename.includes('ldscore') && inputFilename.split(';').length > 1)) ? (
          <button
            id="download-zip-input-btn"
            type="button"
            className="btn btn-default"
            style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }}
            disabled={zipping}
            onClick={async () => {
              const files = filename.includes('ldscore')
                ? inputFilename.split(';').map(f => f.trim()).filter(Boolean)
                : inputFilename.split(',').map(f => f.trim()).filter(Boolean);
              setZipping(true);
              try {
                const res = await fetch('/LDlinkRestWeb/zip', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ files }),
                });
                if (res.ok) {
                     const blob = await res.blob();
                   const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = 'files.zip'; //
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => { document.body.removeChild(a); }, 0);
                  
                }
              } finally {
                setZipping(false);
              }
            }}
          >
            {zipping ? 'Zipping...' : 'Download Inputs'}
          </button>
        ) : inputFilename && (
          <button
            id="download-herit-input-btn"
            type="button"
            className="btn btn-default"
            style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }}
            onClick={() => {
              const a = document.createElement('a');
              a.href = `/LDlinkRestWeb/tmp/uploads/${encodeURIComponent(inputFilename)}`;
              a.download = inputFilename;
              document.body.appendChild(a);
              a.click();
              setTimeout(() => {
                document.body.removeChild(a);
              }, 0);
            }}
          >
            Download Input
          </button>
        )}
       
        <button
          id="download-herit-tables-btn"
          type="button"
          className="btn btn-default"
          style={{ border: '1px solid #bdbdbd', borderRadius: 4, background: '#fff' }}
          onClick={() => {
            const text = parsedTableText || result;
            const blob = new Blob([text], { type: 'text/plain' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
              document.body.removeChild(a);
              URL.revokeObjectURL(a.href);
            }, 0);
          }}
        >
          Download Table
        </button>

      </div>
    </div>
  );
}

// Parse LD Score result into summary and correlation matrix tables
function parseLdScoreResult(result: string) {
  // Find summary section
  const summaryMatch = result.match(/Summary of LD Scores[^\n]*\n([\s\S]+?)\n\s*MAF\/LD Score Correlation Matrix/);
  const corrMatch = result.match(/MAF\/LD Score Correlation Matrix\n([\s\S]+)/);
  const summary = summaryMatch ? summaryMatch[1].trim() : '';
  const corr = corrMatch ? corrMatch[1].trim() : '';
  return { summary, corr };
}

function renderLdScoreTable(section: string, opts?: { ignoreAnalysisFinished?: boolean }) {
  if (!section) return null;
  let lines = section.split(/\r?\n/).filter(l => l.trim());
  if (opts?.ignoreAnalysisFinished) {
    const idx = lines.findIndex(l => /^Analysis\s+finished\s+at/i.test(l));
    if (idx !== -1) lines = lines.slice(0, idx);
  }
  if (lines.length < 2) return <pre>{section}</pre>;
  const header = ['', ...lines[0].split(/\s+/)]; // Add empty string as first element
  const rows = lines.slice(1).map(l => l.split(/\s+/));
  return (
    <TableContainer>
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0, width: 'auto', tableLayout: 'auto', maxWidth: '100%' }}>
        <thead>
          <tr>{header.map((h, i) => <th key={i} style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', backgroundColor: 'rgb(242, 242, 242)', fontWeight: 600 }}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((cols, i) => <tr key={i}>{cols.map((c, j) => <td key={j} style={{ border: '1px solid black', padding: '4px 8px', textAlign: 'left', fontSize: '0.97em' }}>{c}</td>)}</tr>)}
        </tbody>
      </table>
    </TableContainer>
  );
}

export default function LdScoreResults({ reference, type, uploads }: { reference: string, type: 'heritability' | 'correlation' | 'ldscore', uploads: string }) {
  const searchParams = useSearchParams();
  const ref = searchParams.get("ref");

  const { data, isLoading, error } = useQuery({
    queryKey: ["ldscore", ref],
    enabled: !!ref,
  });

  // Fetch result from backend using reference
  const resultQueryKey = ["ldscore_results", reference];
  let resultUrl = "";
  if (type === "heritability") {
    resultUrl = `/LDlinkRestWeb/tmp/ldherit_${reference}.txt`;
  } else if (type === "correlation") {
    resultUrl = `/LDlinkRestWeb/tmp/ldcorrelation_${reference}.txt`;
  } else {
    resultUrl = `/LDlinkRestWeb/tmp/ldscore_${reference}.txt`;
  }
  const { data: result, error: resultError, isLoading: resultLoading } = useSuspenseQuery<string>({
    queryKey: resultQueryKey,
    queryFn: async () => {
      const res = await fetch(resultUrl);
      console.log(res)
      if (!res.ok) throw new Error('Result not found');
      const text = await res.text();
      console.log("Fetched result text:", text);
      return text;
    },
  });

  if (isLoading || resultLoading) {
    return (
      <Container>
        <Row>
          <Col className="text-center">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
            <p>Processing LDscore calculation...</p>
          </Col>
        </Row>
      </Container>
    );
  }

  if (error || resultError) {
    return (
      <Container>
        <Alert variant="danger">
          <Alert.Heading>Error</Alert.Heading>
          <p>Failed to load LDscore results.</p>
        </Alert>
      </Container>
    );
  }

  if ( !result) {
    return null;
  }
  console.log("LDscore result:", result);
  if (type === 'heritability') {
    const inputFilename = uploads;
    const parsedTableText = formatHeritabilityTableText(result);
    return (
      <Container style={{ maxWidth: 600 }}>
        <h5>Heritability Result</h5>
        <HeritabilityResultTable result={result} />
        <DownloadOptionsPanel result={result} filename="heritability_result.txt" inputFilename={inputFilename} parsedTableText={parsedTableText} />
        <CollapsibleRawPanel result={result} title="Heritability Analysis Output" />
      </Container>
    );
  }
  if (type === 'correlation') {
    const parsed = parseGeneticCorrelationResult(result);
    const parsedTableText = formatGeneticCorrelationTableText(parsed);
    const inputFilename = uploads;
    return (
      <Container style={{ maxWidth: 600 }}>
        <h6>Heritability of phenotype 1</h6>
        {renderKeyValueTable(parsed.herit1 || '')}
        <h6>Heritability of phenotype 2</h6>
        {renderKeyValueTable(parsed.herit2 || '')}
        <h6>Genetic Covariance</h6>
        {renderKeyValueTable(parsed.gencov || '')}
        <h6>Genetic Correlation</h6>
        {renderKeyValueTable(parsed.gencorr || '')}
        <h6>Summary of Genetic Correlation Results</h6>
        {renderSummaryTable(parsed.summary || '')}
        <DownloadOptionsPanel result={result} filename="genetic_correlation_result.txt" inputFilename={inputFilename} parsedTableText={parsedTableText} />
        <CollapsibleRawPanel result={result} title="Genetic Correlation Output" />
      </Container>
    );
  }
  // LD Score calculation (raw output)
   if (type === 'ldscore'){
    const parsed = parseLdScoreResult(result);
    // Compose a plain text version of the summary and correlation matrix for download
    const inputFilename = uploads;
    const parsedTableText = [
      "Summary of LD Scores",
      parsed.summary,
      "",
      "MAF/LD Score Correlation Matrix",
      parsed.corr
    ].filter(Boolean).join('\n\n');
    return (
      <Container style={{ maxWidth: 600 }}>
        <h6>Summary of LD Scores</h6>
        {renderLdScoreTable(parsed.summary)}
        <h6>MAF/LD Score Correlation Matrix</h6>
        {renderLdScoreTable(parsed.corr, { ignoreAnalysisFinished: true })}
        <DownloadOptionsPanel result={result} filename="ldscore_result.txt" inputFilename={inputFilename} parsedTableText={parsedTableText} />
        <CollapsibleRawPanel result={result} title="LD Score Calculation Output" />
      </Container>
    );
   }

}
