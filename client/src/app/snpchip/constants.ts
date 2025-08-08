import { snpchipPlatforms } from "@/services/queries";

// Cache for platform data to avoid repeated API calls
const platformCache: {
  platformLookup: Record<string, string> | null;
  codeToPlatform: Record<string, string> | null;
} = {
  platformLookup: null,
  codeToPlatform: null,
};

// Generate PLATFORM_LOOKUP from API response
export const generatePlatformLookup = async (): Promise<Record<string, string>> => {
  if (platformCache.platformLookup) {
    return platformCache.platformLookup;
  }

  try {
    const platforms = await snpchipPlatforms() as Record<string, string>;
    // Convert from { "A_10X": "Affymetrix Mapping 10K Xba142" } 
    // to { "Affymetrix Mapping 10K Xba142": "A_10X" }
    const lookup: Record<string, string> = {};
    for (const [code, fullName] of Object.entries(platforms)) {
      lookup[fullName] = code;
    }
    platformCache.platformLookup = lookup;
    return lookup;
  } catch (error) {
    console.error("Failed to generate platform lookup:", error);
    return {};
  }
};

// Generate CODE_TO_PLATFORM from API response
export const generateCodeToPlatform = async (): Promise<Record<string, string>> => {
  if (platformCache.codeToPlatform) {
    return platformCache.codeToPlatform;
  }

  try {
    const platforms = await snpchipPlatforms() as Record<string, string>;
    // Return as-is since API already provides { "A_10X": "Affymetrix Mapping 10K Xba142" }
    platformCache.codeToPlatform = platforms;
    return platforms;
  } catch (error) {
    console.error("Failed to generate code to platform mapping:", error);
    return {};
  }
};

// Initialize and export the dynamic constants
export let PLATFORM_LOOKUP: Record<string, string> = {};
export let CODE_TO_PLATFORM: Record<string, string> = {};

// Initialize the constants on module load
(async () => {
  try {
    PLATFORM_LOOKUP = await generatePlatformLookup();
    CODE_TO_PLATFORM = await generateCodeToPlatform();
  } catch (error) {
    console.error("Failed to initialize platform constants:", error);
  }
})();
