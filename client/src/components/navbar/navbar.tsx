"use client";
import { usePathname } from "next/navigation";
import Link from "next/link";
import Container from "react-bootstrap/Container";
import Nav from "react-bootstrap/Nav";
import Navbar from "react-bootstrap/Navbar";
import clsx from "clsx";
import React, { useState, useEffect } from "react";
import type { Route } from "../header";

type AppNavbarProps = {
  routes: Route[];
};

// Utility functions
const pathsMatch = (path1: string, path2: string): boolean => {
  if (!path1 || !path2) return false;
  
  const normalize = (path: string) => path.replace(/\/$/, "").toLowerCase();
  return normalize(path1) === normalize(path2);
};

const isRouteActive = (route: Route, pathName: string): boolean => {
  if (route.path && pathsMatch(pathName, route.path)) return true;
  
  return route.subRoutes?.some(subRoute => pathsMatch(pathName, subRoute.path)) ?? false;
};

// Dropdown menu component
const DropdownMenu = ({ 
  route, 
  isActive, 
  pathName, 
  isOpen, 
  onToggle, 
  onClose, 
  isMobile 
}: {
  route: Route;
  isActive: boolean;
  pathName: string;
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  isMobile: boolean;
}) => {
  const handleMouseEvents = isMobile ? {} : {
    onMouseEnter: onToggle,
    onMouseLeave: onClose
  };

  return (
    <Nav.Item 
      className="dropdown position-relative" 
      {...handleMouseEvents}
    >
      <button
        type="button"
        className={clsx(
          "nav-link border-0 text-nowrap pointer-cursor",
          isActive && "nav-menu-active"
        )}
        aria-haspopup="true"
        aria-expanded={isOpen}
        onClick={isMobile ? onToggle : undefined}
      >
        {route.title}
        <i className="bi bi-caret-down-fill ms-1" />
      </button>

      {isOpen && (
        <div className={clsx(
          "dropdown-menu show bg-white border submenu",
          isMobile ? "position-static mt-2" : "position-absolute"
        )}>
          {route.subRoutes.map((subRoute) => (
            <Link
              key={subRoute.path}
              href={subRoute.path}
              className={clsx(
                "dropdown-item",
                pathsMatch(pathName, subRoute.path) ? "active" : "text-dark"
              )}
              onClick={onClose}
            >
              {subRoute.title}
            </Link>
          ))}
        </div>
      )}
    </Nav.Item>
  );
};

// Regular nav item component
const NavItem = ({ route, isActive, onClose }: {
  route: Route;
  isActive: boolean;
  onClose: () => void;
}) => (
  <Nav.Item>
    <Link
      href={route.path || "#"}
      className={clsx(
        "nav-link text-nowrap pointer-cursor",
        isActive && "nav-menu-active"
      )}
      onClick={onClose}
    >
      {route.title}
    </Link>
  </Nav.Item>
);

// Main navbar component
export default function AppNavbar({ routes = [] }: AppNavbarProps) {
  const pathName = usePathname();
  const [openSubmenu, setOpenSubmenu] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const closeMenu = () => setOpenSubmenu(null);
  
  const toggleSubmenu = (title: string) => {
    setOpenSubmenu(openSubmenu === title ? null : title);
  };

  return (
    <Navbar data-bs-theme="dark" className="font-title" expand="md">
      <Container>
        <Navbar.Toggle aria-controls="navbar-nav" className="px-0 py-3">
          <i className="bi bi-list me-1" />
          Menu
        </Navbar.Toggle>
        
        <Navbar.Collapse id="navbar-nav" className="align-items-stretch">
          <Nav className="me-auto">
            {routes.map((route) => {
              const isActive = isRouteActive(route, pathName);
              const hasSubRoutes = route.subRoutes?.length > 0;

              if (!hasSubRoutes) {
                return (
                  <NavItem 
                    key={route.path || route.title}
                    route={route} 
                    isActive={isActive} 
                    onClose={closeMenu} 
                  />
                );
              }

              return (
                <DropdownMenu
                  key={route.title}
                  route={route}
                  isActive={isActive}
                  pathName={pathName}
                  isOpen={openSubmenu === route.title}
                  onToggle={() => toggleSubmenu(route.title)}
                  onClose={closeMenu}
                  isMobile={isMobile}
                />
              );
            })}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}
