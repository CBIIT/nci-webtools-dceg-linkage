import Image from "next/image";

export default function CalculateLoading() {
  return (
    <div className="loader text-center">
      <Image
        src="/images/calculating_LD.gif"
        alt="Calculating LD"
        width={130}
        height={0}
        style={{
          maxWidth: "100%",
          height: "auto",
        }}
      />
    </div>
  );
}
