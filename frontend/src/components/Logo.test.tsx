import { describe, it, expect } from 'vitest';
import { render, screen } from '../test/test-utils';
import Logo from './Logo';

describe('Logo Component', () => {
  it('renders the logo image', () => {
    render(<Logo />);
    const logoImage = screen.getByAltText('DataVision');
    expect(logoImage).toBeInTheDocument();
  });

  it('displays text by default', () => {
    render(<Logo />);
    expect(screen.getByText('Data')).toBeInTheDocument();
    expect(screen.getByText('Vision')).toBeInTheDocument();
  });

  it('hides text when showText is false', () => {
    render(<Logo showText={false} />);
    expect(screen.queryByText('Data')).not.toBeInTheDocument();
    expect(screen.queryByText('Vision')).not.toBeInTheDocument();
  });

  it('applies correct size for sm', () => {
    render(<Logo size="sm" />);
    const logoImage = screen.getByAltText('DataVision');
    expect(logoImage).toHaveStyle({ width: '28px', height: '28px' });
  });

  it('applies correct size for md', () => {
    render(<Logo size="md" />);
    const logoImage = screen.getByAltText('DataVision');
    expect(logoImage).toHaveStyle({ width: '36px', height: '36px' });
  });

  it('applies correct size for lg', () => {
    render(<Logo size="lg" />);
    const logoImage = screen.getByAltText('DataVision');
    expect(logoImage).toHaveStyle({ width: '48px', height: '48px' });
  });

  it('applies correct size for xl', () => {
    render(<Logo size="xl" />);
    const logoImage = screen.getByAltText('DataVision');
    expect(logoImage).toHaveStyle({ width: '64px', height: '64px' });
  });

  it('applies custom className', () => {
    render(<Logo className="custom-class" />);
    const container = screen.getByAltText('DataVision').parentElement;
    expect(container).toHaveClass('custom-class');
  });
});
