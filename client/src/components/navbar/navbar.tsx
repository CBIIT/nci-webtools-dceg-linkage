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
    <div className={clsx("d-flex flex-row", !isOpen && "d-none", isMainActive && "active-submenu")}>
      {subRoutes.map((subRoute: { path: string; title: string }) => (
        <Nav.Item key={subRoute.path}>
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
  handleOpenSubmenu,
  handleCloseSubmenu,
  isMobileView,
}: {
  routes: Route[];
  pathName: string;
  openSubmenu: string | null;
  handleOpenSubmenu: (event: MouseEvent, title: string, subRoutes: Array<{ path: string; title: string }>) => void;
  handleCloseSubmenu: () => void;
  isMobileView: boolean;
}): React.ReactElement[] {
  return routes.map((route) => (
    <div key={route.path || route.title}>
      {route.subRoutes.length == 0 ? (
        <Nav.Item className="">
          <Link
            href={route.path}
            className={clsx("nav-link", isRouteActive(route, pathName) && "nav-menu-active", "pointer-cursor")}
            onClick={() => {
              // Add the 'nav-menu-active' class to the clicked item
              document.querySelectorAll(".navbar-nav .nav-link .nav-menu-active").forEach((link) => {
                link.classList.remove("nav-menu-active");
              });

              const currentLink = document.querySelector(`.nav-item a[href="${route.path}"]`);

              if (currentLink) {
                currentLink.classList.add("nav-menu-active");
              }
              handleCloseSubmenu();
            }}>
            {route.title}
          </Link>
        </Nav.Item>
      ) : (
        <div
          className={clsx(
            "nav-link",
            (openSubmenu === route.title || isRouteActive(route, pathName)) &&
              "nav-menu-active",
            "pointer-cursor"
          )}>
          <div
            onClick={(e) => {
              handleOpenSubmenu(e, route.title, route.subRoutes);
              // Unhighlight all other navbar items with a path
              document.querySelectorAll(".navbar-nav .nav-link.nav-menu-active").forEach((link) => {
                link.classList.remove("nav-menu-active");
              });
            }}>
            {route.title}
          </div>
          {route.subRoutes && isMobileView && (
            <div className="submenu">
              <SubMenu
                subRoutes={route.subRoutes}
                pathName={pathName}
                isOpen={openSubmenu === route.title || isRouteActive(route, pathName)}
                isMainActive={isRouteActive(route, pathName)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  ));
}

// Main AppNavbar component
export default function AppNavbar({ routes = [] }: AppNavbarProps): React.ReactElement {
  const pathName = usePathname();
  const [openSubmenu, setOpenSubmenu] = useState<string | null>(null);
  const [isMobileView, setIsMobileView] = useState<boolean>(false);
  const router = useRouter(); // Move the useRouter hook to the main component
  const handleSubmenuClick = (path: string) => {
    router.push(path);
  };

  const handleOpenSubmenu = (
    event: MouseEvent,
    title: string,
    subRoutes: Array<{ path: string; title: string }>
  ) => {
    event.preventDefault();
    setOpenSubmenu((prevOpenSubmenu) => {
      // Set the first subRoute as the default open submenu
      handleSubmenuClick(subRoutes[0].path);
      return title;
    });
  };

  const handleCloseSubmenu = (): void => {
    setOpenSubmenu(null);
  };

  // Check for mobile view
  React.useEffect(() => {
    const handleResize = () => {
      setIsMobileView(window.innerWidth <= 768); // Adjust the breakpoint as needed
    };

    handleResize(); // Set initial view
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <div>
      {/* Main Navbar */}
      <Navbar bg="dark" data-bs-theme="dark" className="text-uppercase font-title" expand="md">
        <Container>
          {/* Navbar Brand and Toggle */}
          <Navbar.Toggle aria-controls="navbar-nav" className="px-0 py-3 text-uppercase">
            <i className="bi bi-list me-1"></i>
            Menu
          </Navbar.Toggle>
          {/* Navbar Content */}
          <Navbar.Collapse id="navbar-nav" className="align-items-stretch">
            <Nav className="me-auto">
              {/* Render routes */}
              {renderRoutes({
                routes,
                pathName,
                openSubmenu,
                handleOpenSubmenu,
                handleCloseSubmenu,
                isMobileView, // Pass isMobileView prop
              })}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      {/* Subnavbar */}
      <div className="submenu-border">
        <div className="text-uppercase font-title">
          <Container className="">
            <Nav className="me-auto">
              {/* Render submenus */}
              {routes.map((route) => (
                <div key={route.title}>
                  {route.subRoutes && (
                    <div className="submenu">
                      <SubMenu
                        subRoutes={route.subRoutes}
                        pathName={pathName}
                        isOpen={openSubmenu === route.title}
                        isMainActive={isRouteActive(route, pathName)}
                      />
                    </div>
                  )}
                </div>
              ))}
            </Nav>
          </Container>
        </div>
      </div>
    </div>
  );
}
