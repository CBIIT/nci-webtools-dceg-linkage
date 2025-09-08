import { Container, Row, Col } from "react-bootstrap";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import Image from "next/image";
import WhatsNew from "@/components/home/whatsnew";
import LdToolSection from "@/components/home/ldToolCards";

export default function Home() {
  const searchParams = useSearchParams();
  const router = useRouter();
  // Client-side fallback redirect if middleware not applied (e.g., static export or dev env)
  useEffect(() => {
    if (searchParams?.has("snps") && searchParams.get("tab") === "ldtraitget") {
      const params = new URLSearchParams();
      const copyKeys = ["snps", "pop", "r2_d", "window", "genome_build", "r2_d_threshold"] as const;
      copyKeys.forEach(k => {
        const v = searchParams.get(k);
        if (v) params.set(k, v);
      });
      if (!params.has("r2_d")) params.set("r2_d", "r2");
      if (!params.has("window")) params.set("window", "500000");
      if (!params.has("genome_build")) params.set("genome_build", "grch37");
      if (!params.has("r2_d_threshold")) params.set("r2_d_threshold", "0.1");
      router.replace(`/ldtrait?${params.toString()}`);
    }
    if (searchParams?.has("snps") && searchParams.get("tab") === "ldexpressget") {
      const params = new URLSearchParams();
      const copyKeys = ["snps", "pop", "tissues", "r2_d", "p_threshold", "r2_d_threshold", "window", "genome_build"] as const;
      copyKeys.forEach(k => {
        const v = searchParams.get(k);
        if (v) params.set(k, v);
      });
      if (!params.has("r2_d")) params.set("r2_d", "r2");
      if (!params.has("p_threshold")) params.set("p_threshold", "0.1");
      if (!params.has("r2_d_threshold")) params.set("r2_d_threshold", "0.1");
      if (!params.has("window")) params.set("window", "500000");
      if (!params.has("genome_build")) params.set("genome_build", "grch37");
      params.set("autorun", "1");
      router.replace(`/ldexpress?${params.toString()}`);
    }
  }, [searchParams, router]);
  return (
    <>
      <Container>
        <Row className="mt-3">
          <Col className="text-center">
            <h1>
              Welcome to{" "}
              <Image
                src="/images/LDlink_logo_small_clear.png"
                alt="LDlink"
                style={{ verticalAlign: "bottom" }}
                width={91}
                height={36}
              />
            </h1>
          </Col>
        </Row>

        <Row className="mb-4">
          <Col className="text-center" style={{ maxWidth: "1200px", margin: "auto" }}>
            <p>
              LDlink is a suite of web-based applications designed to easily and efficiently interrogate linkage
              disequilibrium in population groups. Each included application is specialized for querying and displaying
              unique aspects of linkage disequilibrium.
            </p>
          </Col>
        </Row>
        <Row>
          <Col>
            <LdToolSection />
          </Col>
        </Row>

        <Row className="mb-4">
          <Col>
            <WhatsNew />
          </Col>
        </Row>

        <Row>
          <Col>
            <Container>
              <p style={{ fontSize: "18px" }}>
                <b>Credits</b>
              </p>
              <p>
                {" "}
                LDlink was developed by{" "}
                <a
                  href="https://dceg.cancer.gov/about/staff-directory/biographies/K-N/machiela-mitchell"
                  title="Mitchell Machiela Biography"
                  target="_blank">
                  Mitchell Machiela
                </a>{" "}
                in collaboration with NCI&apos;s Center for Biomedical Informatics and Information Technology (CBIIT).
                Support comes from the Division of Cancer Epidemiology and Genetics Informatics Tool Challenge.
              </p>
              <p>
                This work utilized the computational resources of the NIH STRIDES Initiative (
                <a href="https://cloud.nih.gov" target="_blank">
                  https://cloud.nih.gov
                </a>
                ) through the Other Transaction agreement [AWS&#123;*&#125;:&#123;*&#125; OT2OD027852]
              </p>
              <p>
                LDlink&apos;s{" "}
                <a href="https://github.com/CBIIT/nci-webtools-dceg-linkage" target="_blank">
                  source code
                </a>{" "}
                is available under the{" "}
                <a href="license.txt" target="_blank">
                  MIT license
                </a>
                , an{" "}
                <a href="https://opensource.org" target="_blank">
                  Open Source Initiative
                </a>{" "}
                approved license.
              </p>
              <p>
                Questions or comments? Contact us via{" "}
                <a href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink" target="_top" title="Support">
                  email
                </a>
                .
              </p>
            </Container>
          </Col>
        </Row>
      </Container>
    </>
  );
}
