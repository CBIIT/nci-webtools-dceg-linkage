import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Page from '../src/app/page'
 
describe('Home page', () => {
  it('renders the home page content', () => {
    render(<Page />)

    // Check for heading
    const heading = screen.getByRole('heading', { level: 2, name: /Welcome to/i })
    expect(heading).toBeInTheDocument()

    // Check for introductory paragraph
    const paragraph = screen.getByText(
      /LDlink is a suite of web-based applications designed to easily and efficiently interrogate linkage disequilibrium in population groups/i
    )
    expect(paragraph).toBeInTheDocument()

    // Check for Credits section
    const creditsHeading = screen.getByText('Credits')
    expect(creditsHeading).toBeInTheDocument()

    const machielaLink = screen.getByText('Mitchell Machiela')
    expect(machielaLink).toBeInTheDocument()
    expect(machielaLink.closest('a')).toHaveAttribute('href', 'https://dceg.cancer.gov/about/staff-directory/biographies/K-N/machiela-mitchell')

    const sourceCodeLink = screen.getByText('source code')
    expect(sourceCodeLink).toBeInTheDocument()
    expect(sourceCodeLink.closest('a')).toHaveAttribute('href', 'https://github.com/CBIIT/nci-webtools-dceg-linkage')

    const licenseLink = screen.getByText('MIT license')
    expect(licenseLink).toBeInTheDocument()
    expect(licenseLink.closest('a')).toHaveAttribute('href', 'license.txt')

    const osiLink = screen.getByText('Open Source Initiative')
    expect(osiLink).toBeInTheDocument()
    expect(osiLink.closest('a')).toHaveAttribute('href', 'https://opensource.org')

    const emailLink = screen.getByText('email')
    expect(emailLink).toBeInTheDocument()
    expect(emailLink.closest('a')).toHaveAttribute('href', 'mailto:NCILDlinkWebAdmin@mail.nih.gov?subject=LDlink')
  })
})