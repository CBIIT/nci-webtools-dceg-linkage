"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import clsx from "clsx";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import type { Route } from "../header";
import type { MouseEvent } from "react";
import { NavDropdown } from "react-bootstrap";

type AppNavbarProps = {
  routes: Route[];
};

function pathsMatch(path1: string, path2: string) {
  // Check if path1 or path2 is undefined
  if (!path1 || !path2) {
    return false;
  }

  // remove trailing slash
  path1 = path1.replace(/\/$/, "");
  path2 = path2.replace(/\/$/, "");

  return path1 === path2;
}

function SubMenu({
  subRoutes,
  pathName,
  isOpen,
  isMainActive,
}: {
  subRoutes: Array<{ path: string; title: string }>;
  pathName: string;
  isOpen: boolean;
  isMainActive: boolean;
}): React.ReactElement {
  return (
    <div className={clsx("d-flex flex-column", !isOpen && "d-none", isMainActive && "active-submenu")}>
      {subRoutes.map((subRoute: { path: string; title: string }) => (
        <Nav.Item key={subRoute.path} className="mb-1">
          <Link
            href={subRoute.path || "#"}
            className={clsx("nav-link", "submenu", pathsMatch(pathName, subRoute.path) && "active")}>
            {subRoute.title}
          </Link>
        </Nav.Item>
      ))}
    </div>
  );
}

function isRouteActive(route: Route, pathName: string): boolean {
  if (route.path && pathsMatch(pathName, route.path)) {
    return true;
  }

  if (route.subRoutes) {
    const isSubRouteActive = route.subRoutes.some((subRoute: { path: string }) => {
      const isActive = pathsMatch(pathName, subRoute.path);

      return isActive;
    });

    if (isSubRouteActive) {
      return true;
    }
  }

  return false;
}

// Function to render routes
function renderRoutes({
  routes,
  pathName,
  openSubmenu,
  setOpenSubmenu,
  isMobileView,
}: {
  routes: Route[];
  pathName: string;
  openSubmenu: string | null;
  setOpenSubmenu: (title: string | null) => void;
  isMobileView: boolean;
}): React.ReactElement[] {
  return routes.map((route) => {
    const isActive = isRouteActive(route, pathName);
    const hasSubRoutes = route.subRoutes && route.subRoutes.length > 0;

    if (!hasSubRoutes) {
      return (
        <Nav.Item key={route.path || route.title}>
          <Link href={route.path} className={clsx("nav-link", isActive && "nav-menu-active", "pointer-cursor")}>
            {route.title}
          </Link>
        </Nav.Item>
      );
    }

    const handleClickMobile = () => {
      if (isMobileView) {
        setOpenSubmenu(openSubmenu === route.title ? null : route.title);
      }
    };

    let closeTimer: NodeJS.Timeout;

    return (
      <div
        key={route.title}
        onMouseEnter={() => {
          if (!isMobileView) {
            clearTimeout(closeTimer);
            setOpenSubmenu(route.title);
          }
        }}
        onMouseLeave={() => {
          if (!isMobileView) {
            closeTimer = setTimeout(() => {
              setOpenSubmenu(null);
            }, 200); // 200ms delay
          }
        }}
        style={{ position: "relative" }}
      >
        <NavDropdown
          title={route.title}
          id={`nav-dropdown-${route.title}`}
          show={openSubmenu === route.title}
          onClick={() => {
            if (isMobileView) {
              setOpenSubmenu(openSubmenu === route.title ? null : route.title);
            }
          }}
          className={clsx(isActive && "nav-menu-active")}
        >
          {route.subRoutes.map((subRoute) => (
            <NavDropdown.Item
              key={subRoute.path}
              href={subRoute.path}
              active={pathsMatch(pathName, subRoute.path)}
            >
              {subRoute.title}
            </NavDropdown.Item>
          ))}
        </NavDropdown>
      </div>
    );


  });
}

// Main AppNavbar component
export default function AppNavbar({ routes = [] }: AppNavbarProps): React.ReactElement {
  const pathName = usePathname();
  const [openSubmenu, setOpenSubmenu] = useState<string | null>(null);
  const [isMobileView, setIsMobileView] = useState<boolean>(false);

  React.useEffect(() => {
    const handleResize = () => {
      setIsMobileView(window.innerWidth <= 768);
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <Navbar expand="md" className="text-uppercase font-title">
      <Container>
        <Navbar.Toggle aria-controls="navbar-nav" className="px-0 py-3 text-uppercase">
          <i className="bi bi-list me-1"></i> Menu
        </Navbar.Toggle>
        <Navbar.Collapse id="navbar-nav" className="align-items-stretch">
          <Nav className="me-auto">
            {renderRoutes({ routes, pathName, openSubmenu, setOpenSubmenu, isMobileView })}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
