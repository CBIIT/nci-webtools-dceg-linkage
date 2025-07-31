"use client";
import React, { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { Container, Row, Col, Alert, Spinner } from "react-bootstrap";

// Helper functions for parsing and rendering results (copied from form.tsx, can be improved)
function parseHeritabilityResult(result: string) {
  const h2Match = result.match(/Total Observed scale h2:\s*([\d.eA-Z+-]+) \(([^)]+)\)/);
  const lambdaMatch = result.match(/Lambda GC:\s*([\d.eA-Z+-]+)/);
  const meanChi2Match = result.match(/Mean Chi\^2:\s*([\d.eA-Z+-]+)/);
  const interceptMatch = result.match(/Intercept:\s*([\d.eA-Z+-]+) \(([^)]+)\)/);
  const ratioMatch = result.match(/Ratio\s*([<>=-]*)\s*([\d.eA-Z+-]+)/);
  return {
    h2: h2Match ? `${h2Match[1]} (${h2Match[2]})` : "",
    lambdaGC: lambdaMatch ? lambdaMatch[1] : "",
    meanChi2: meanChi2Match ? meanChi2Match[1] : "",
    intercept: interceptMatch ? `${interceptMatch[1]} (${interceptMatch[2]})` : "",
    ratio: ratioMatch ? `${ratioMatch[1]} ${ratioMatch[2]}` : "",
  };
}

function parseGeneticCorrelationResult(resultStr: string) {
  const startIdx = resultStr.search(/Heritability of phenotype 1/i);
  if (startIdx === -1) return {};
  const trimmed = resultStr.slice(startIdx);
  const headers = [
    'Heritability of phenotype 1',
    'Heritability of phenotype 2',
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
    herit2: sections['Heritability of phenotype 2'] || '',
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
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0 }}>
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
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0 }}>
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
      <table className="table table-bordered table-sm mb-3" style={{ margin: 0, minWidth: 0 }}>
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

export default function LdScoreResults({ reference, type }: { reference: string, type: 'heritability' | 'correlation' | 'ldscore' }) {
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

  // if (!data || !result) {
  //   return null;
  // }

  if (type === 'heritability') {
    return (
      <Container style={{ maxWidth: 600 }}>
        <h5>Heritability Result</h5>
        <HeritabilityResultTable result={result} />
        <CollapsibleRawPanel result={result} title="Heritability Analysis Output" />
      </Container>
    );
  }
  if (type === 'correlation') {
    const parsed = parseGeneticCorrelationResult(result);
    return (
      <Container style={{ maxWidth: 600 }}>
        <h5>Heritability of phenotype 1</h5>
        {renderKeyValueTable(parsed.herit1 || '')}
        <h5>Heritability of phenotype 2</h5>
        {renderKeyValueTable(parsed.herit2 || '')}
        <h5>Genetic Covariance</h5>
        {renderKeyValueTable(parsed.gencov || '')}
        <h5>Genetic Correlation</h5>
        {renderKeyValueTable(parsed.gencorr || '')}
        <h5>Summary of Genetic Correlation Results</h5>
        {renderSummaryTable(parsed.summary || '')}
        <pre style={{ background: '#f9f9f9', padding: 12, borderRadius: 6 }}>{result}</pre>
      </Container>
    );
  }
  // LD Score calculation (raw output)
  return (
    <Container style={{ maxWidth: 600 }}>
      <h5>LD Score Calculation Result</h5>
      <pre style={{ background: '#f9f9f9', padding: 12, borderRadius: 6 }}>{result}</pre>
    </Container>
  );
}
