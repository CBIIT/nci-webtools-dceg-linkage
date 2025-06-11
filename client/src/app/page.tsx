import Link from "next/link";
import { Container, Row, Col } from "react-bootstrap";

export default function Home() {
  return (
    <>
      <div className="bg-primary flex-grow-1">
        <Container>
          <Row>
            <Col md={6}>
              <div className="d-flex h-100 align-items-center" style={{ minHeight: "300px" }}>
                <div>
                  <h1 className="fs-1 text-light fw-light mb-3">LDlink</h1>
                  <hr className="border-white" />
                  <p className="lead text-light">DCEG Linkage</p>

                  <Link className="link-secondary" href="/citations">
                    Citations
                  </Link>
                </div>
              </div>
            </Col>
          </Row>
        </Container>
      </div>
      <div className="bg-light py-5 flex-grow-1">
        <Container>
          <Row>
            <Col>
              <p>
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aliquam id dictum sapien. Nam suscipit erat vel
                facilisis sagittis. Fusce a ante sed magna malesuada tincidunt. Ut pretium, ante eget suscipit egestas,
                augue ligula vestibulum justo, id interdum nunc odio et odio. Sed sed egestas nisl, aliquam imperdiet
                quam. Duis pellentesque purus cursus, molestie felis eget, facilisis nisl. Phasellus convallis lectus
                vitae nibh imperdiet commodo. Integer rhoncus imperdiet mauris. Suspendisse at dolor felis. Vestibulum
                ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Nam imperdiet elit orci,
                nec condimentum lectus sollicitudin eu. Aenean felis nunc, accumsan a arcu ut, sagittis ornare lorem.
                Sed ac lorem et dui faucibus pharetra vel sed ipsum. Quisque varius erat euismod dolor lacinia commodo.
                Phasellus sed ultrices neque, sit amet consectetur nisl.
              </p>
              <div>
                <p className="h6">Reference</p>
                <ol>
                  <li>
                    Sed fringilla elementum convallis. Morbi vehicula sapien sit amet quam facilisis, id gravida massa
                    volutpat. Nulla venenatis aliquam mi eu finibus. Proin at congue magna, in tempor dui. Suspendisse
                    potenti. Quisque pharetra sagittis volutpat. Suspendisse laoreet risus et tempor sollicitudin.
                  </li>
                </ol>
              </div>
            </Col>
          </Row>
        </Container>
      </div>
    </>
  );
}
