// app/components/Credits.tsx
export default function Credits() {
  return (
    <div className="container mt-4">
      <p style={{ fontSize: "18px" }}>
        <b>Credits</b>
      </p>
      <p>
        LDlink was developed by{" "}
        <a
          href="https://dceg.cancer.gov/about/staff-directory/biographies/K-N/machiela-mitchell"
          target="_blank"
          rel="noopener noreferrer"
        >
          Mitchell Machiela
        </a>{" "}
        in collaboration with NCI&apos;s Center for Biomedical Informatics and Information Technology (CBIIT). Support
        comes from the Division of Cancer Epidemiology and Genetics Informatics Tool Challenge.
      </p>

      <p>
        This work utilized the computational resources of the NIH STRIDES Initiative (
        <a href="https://cloud.nih.gov" target="_blank" rel="noopener noreferrer">
          https://cloud.nih.gov
        </a>
        ) through the Other Transaction agreement [AWS OT2OD027852].
      </p>

      <p>
        LDlink&apos;s{" "}
        <a
          href="https://github.com/CBIIT/nci-webtools-dceg-linkage"
          target="_blank"
          rel="noopener noreferrer"
        >
          source code
        </a>{" "}
        is available under the{" "}
        <a href="license.txt" target="_blank" rel="noopener noreferrer">
          MIT license
        </a>
        , an{" "}
        <a href="https://opensource.org" target="_blank" rel="noopener noreferrer">
          Open Source Initiative
        </a>{" "}
        approved license.
      </p>

      <p>
        Questions or comments? Contact us via{" "}
        <a
          href="mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink"
          target="_top"
          title="Support"
        >
          email
        </a>
        .
      </p>

      <p id="ldlink_version"></p>
    </div>
  );
}
