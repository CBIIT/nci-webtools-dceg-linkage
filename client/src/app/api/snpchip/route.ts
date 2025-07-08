import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

export async function POST(request: Request) {
  const formData = await request.formData();
  const snps = formData.get('snps') as string;
  const file = formData.get('file') as File;
  const genomeBuild = formData.get('genome_build') as string;
  // Platforms are not used yet, but could be in the future
  // const platforms = JSON.parse(formData.get('platforms') as string);

  const uniqueId = `snpchip_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const tmpDir = path.join(os.tmpdir(), 'nci-webtools-dceg-linkage');
  await fs.promises.mkdir(tmpDir, { recursive: true });
  const inputFile = path.join(tmpDir, `${uniqueId}.txt`);
  const outputFile = path.join(tmpDir, `${uniqueId}.json`);

  if (file) {
    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.promises.writeFile(inputFile, buffer);
  } else if (snps) {
    await fs.promises.writeFile(inputFile, snps.trim().replace(/\n/g, '\n'));
  } else {
    return NextResponse.json({ message: 'No SNPs or file provided.' }, { status: 400 });
  }

  const scriptPath = path.resolve(process.cwd(), '../../server/SNPchip.py');
  const pythonPath = 'python3'; // Assuming python3 is in the PATH

  const args = [
    scriptPath,
    inputFile,
    outputFile,
    genomeBuild
  ];

  try {
    const result = await new Promise((resolve, reject) => {
      const process = spawn(pythonPath, args);
      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code !== 0) {
          console.error(`Python script exited with code ${code}`);
          console.error(stderr);
          reject(new Error(`Calculation failed: ${stderr}`));
        } else {
          resolve(stdout);
        }
      });

       process.on('error', (err) => {
        console.error('Failed to start subprocess.');
        reject(err);
      });
    });

    const resultsData = await fs.promises.readFile(outputFile, 'utf-8');
    
    // Clean up temporary files
    await fs.promises.unlink(inputFile);
    await fs.promises.unlink(outputFile);

    return NextResponse.json(JSON.parse(resultsData));

  } catch (error: any) {
    // Clean up temporary files in case of error
    if (fs.existsSync(inputFile)) await fs.promises.unlink(inputFile);
    if (fs.existsSync(outputFile)) await fs.promises.unlink(outputFile);
    
    return NextResponse.json({ message: 'An error occurred during calculation.', error: error.message }, { status: 500 });
  }
}
