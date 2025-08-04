---
applyTo: "client"
---

# LDlink Frontend Development Guidelines

## Project Overview

LDlink is a Next.js 15 web application that provides a suite of tools for interrogating linkage disequilibrium in population groups. The frontend is built with modern React patterns and integrates with a Flask backend API.

## Technology Stack

### Core Technologies
- **Next.js 15.3.3** - React framework with App Router
- **React 19** - UI library
- **TypeScript 5** - Type safety
- **React Bootstrap 2.10.10** - UI components
- **Bootstrap 5.3.6** - CSS framework
- **Sass** - CSS preprocessing

### State Management & Data Fetching
- **Zustand 5.0.6** - Lightweight state management
- **TanStack Query 5.81.2** - Server state management
- **Axios 1.10.0** - HTTP client

### Additional Libraries
- **React Hook Form 7.58.1** - Form handling
- **Bokeh.js 3.7.3** - Data visualization
- **TanStack Table 8.21.3** - Data tables
- **Bootstrap Icons 1.13.1** - Icon library

## Project Structure

```
client/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx         # Root layout with providers
│   │   ├── page.tsx           # Home page
│   │   ├── styles/            # Global styles and themes
│   │   └── [tool]/            # Tool-specific pages
│   │       ├── page.tsx       # Tool main page
│   │       ├── form.tsx       # Tool form component
│   │       ├── results.tsx    # Results display
│   │       └── types.ts       # Tool-specific types
│   ├── components/             # Reusable components
│   │   ├── header.tsx         # Site header with navigation
│   │   ├── footer.tsx         # Site footer
│   │   ├── navbar/            # Navigation components
│   │   ├── cards/             # Card components
│   │   ├── sections/          # Page sections
│   │   ├── select/            # Select components
│   │   └── ldLinkData/        # Data components
│   ├── services/              # API and utility services
│   │   ├── queries.ts         # API query functions
│   │   └── utils.ts           # Utility functions
│   ├── store.ts               # Zustand store configuration
│   └── types/                 # TypeScript type definitions
├── public/                    # Static assets
│   ├── images/                # Images and logos
│   └── files/                 # Data files
└── package.json               # Dependencies and scripts
```

## Coding Standards

### TypeScript
- Use strict TypeScript configuration
- Define proper interfaces for all props and state
- Use type inference where appropriate
- Avoid `any` type when possible (ESLint rule is disabled for legacy code)

### React Patterns
- Use function components with hooks
- Implement proper error boundaries
- Use React Suspense for loading states
- Follow Next.js 15 App Router patterns
- Use "use client" directive for client components

### Component Structure
```typescript
"use client";
import { useState, useEffect } from "react";
import { Container, Row, Col } from "react-bootstrap";

interface ComponentProps {
  // Define props interface
}

export default function ComponentName({ prop1, prop2 }: ComponentProps) {
  // Component logic
  return (
    // JSX
  );
}
```

### State Management
- Use Zustand for global state (genome build, user preferences)
- Use TanStack Query for server state (API data)
- Use React state for local component state
- Use React Hook Form for form state

### API Integration
- All API calls go through `/LDlinkRestWeb/` endpoints
- Use the `queries.ts` service for API calls
- Implement proper error handling
- Use TanStack Query for caching and background updates

## Styling Guidelines

### CSS Framework
- Use Bootstrap 5.3.6 as the primary CSS framework
- Customize Bootstrap variables in `bootstrap-variables.scss`
- Use Bootstrap Icons for icons
- Follow NIH design system patterns

### SCSS Structure
- Main styles in `src/app/styles/main.scss`
- Import order: variables → utils → bootstrap → theme → custom
- Use Bootstrap utility classes when possible
- Custom styles should follow BEM methodology

### Color Scheme
- Primary: NIH blue (#007cba)
- Secondary: Yellow accent (#f5ab35)
- Background: Light gray (#f8f9fa)
- Text: Dark gray (#444)

## Form Handling

### React Hook Form
- Use React Hook Form for all forms
- Implement proper validation
- Handle file uploads with FormData
- Use controlled components for complex inputs

### Form Structure
```typescript
import { useForm } from "react-hook-form";

interface FormData {
  // Define form data interface
}

export default function FormComponent() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>();
  
  const onSubmit = (data: FormData) => {
    // Handle form submission
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
}
```

## Data Visualization

### Bokeh.js Integration
- Use Bokeh.js for complex data visualizations
- Implement proper loading states
- Handle responsive design
- Export functionality with HTML2Canvas

### Table Components
- Use TanStack Table for data tables
- Implement sorting, filtering, and pagination
- Handle large datasets efficiently
- Provide export functionality

## Error Handling

### Error Boundaries
- Implement error boundaries at the page level
- Show user-friendly error messages
- Log errors for debugging
- Provide fallback UI

### API Error Handling
```typescript
try {
  const data = await apiCall(params);
  // Handle success
} catch (error) {
  // Handle error with user-friendly message
  console.error('API Error:', error);
}
```

## Performance Optimization

### Next.js Optimizations
- Use Next.js Image component for images
- Implement proper loading states
- Use dynamic imports for large components
- Optimize bundle size

### React Optimizations
- Use React.memo for expensive components
- Implement proper dependency arrays in useEffect
- Avoid unnecessary re-renders
- Use React Query for efficient data fetching

## Accessibility

### WCAG Compliance
- Use semantic HTML elements
- Implement proper ARIA labels
- Ensure keyboard navigation
- Provide alt text for images
- Maintain proper color contrast

### Screen Reader Support
- Use proper heading hierarchy
- Implement skip links
- Provide descriptive link text
- Use ARIA landmarks

## Testing Guidelines

### Component Testing
- Test component rendering
- Test user interactions
- Test error states
- Test loading states

### Integration Testing
- Test API integration
- Test form submissions
- Test navigation
- Test responsive design

## Deployment

### Environment Configuration
- Use environment variables for API endpoints
- Configure Next.js rewrites for API proxying
- Set up proper build optimization
- Configure static asset serving

### Build Process
```bash
npm run build    # Production build
npm run dev      # Development server
npm run start    # Production server
npm run lint     # Code linting
```

## Common Patterns

### Tool Page Structure
Each LD tool follows this pattern:
1. Main page with form (`page.tsx`)
2. Form component with validation (`form.tsx`)
3. Results display with visualization (`results.tsx`)
4. Type definitions (`types.ts`)

### API Service Pattern
```typescript
export async function toolName(params: ToolParams): Promise<ToolResponse> {
  const searchParams = new URLSearchParams(flattenForParams(params)).toString();
  return (await axios.get(`/LDlinkRestWeb/toolname?${searchParams}`)).data;
}
```

### State Management Pattern
```typescript
// Global state with Zustand
export const useStore = create<StoreState>((set) => ({
  genome_build: "grch37",
  setGenomeBuild: (genome_build: string) => set(() => ({ genome_build })),
}));
```

## Best Practices

1. **Code Organization**: Keep components small and focused
2. **Type Safety**: Use TypeScript interfaces for all data structures
3. **Error Handling**: Implement comprehensive error boundaries
4. **Performance**: Optimize for large datasets and complex visualizations
5. **Accessibility**: Follow WCAG guidelines
6. **Testing**: Write tests for critical user paths
7. **Documentation**: Comment complex logic and API integrations
8. **Security**: Validate all user inputs and sanitize data

## Development Workflow

1. Create feature branch from main
2. Implement changes following coding standards
3. Test with various data scenarios
4. Ensure responsive design works
5. Run linting and type checking
6. Create pull request with detailed description
7. Address review feedback
8. Merge after approval

## Troubleshooting

### Common Issues
- **API Integration**: Check network tab for failed requests
- **Type Errors**: Ensure proper TypeScript interfaces
- **Styling Issues**: Verify Bootstrap class usage
- **Performance**: Use React DevTools for profiling
- **Build Errors**: Check Next.js configuration

### Debug Tools
- React DevTools for component debugging
- Network tab for API debugging
- Console for error logging
- Lighthouse for performance analysis