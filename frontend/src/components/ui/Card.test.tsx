import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import Card, { CardContent, CardActions, CardHeader } from './Card';
import { EmotionThemeProvider } from '../../providers/ThemeProvider';

// Wrapper with theme provider
const WithTheme = ({ children }: { children: React.ReactNode }) => (
  <EmotionThemeProvider>{children}</EmotionThemeProvider>
);

describe('Card Component', () => {
  describe('Basic Rendering', () => {
    it('renders children correctly', () => {
      render(
        <WithTheme>
          <Card>
            <span>Card Content</span>
          </Card>
        </WithTheme>
      );
      expect(screen.getByText('Card Content')).toBeInTheDocument();
    });

    it('applies default elevation', () => {
      const { container } = render(
        <WithTheme>
          <Card>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ boxShadow: expect.stringContaining('rgba') });
    });

    it('applies custom elevation', () => {
      const { container } = render(
        <WithTheme>
          <Card elevation={4}>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ boxShadow: expect.any(String) });
    });

    it('renders as different component when specified', () => {
      const { container } = render(
        <WithTheme>
          <Card component="section">Content</Card>
        </WithTheme>
      );
      expect(container.querySelector('section')).toBeInTheDocument();
    });
  });

  describe('Styling Variants', () => {
    it('renders outlined variant without shadow', () => {
      const { container } = render(
        <WithTheme>
          <Card outlined>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ border: expect.stringContaining('1px solid') });
    });

    it('renders bordered variant', () => {
      const { container } = render(
        <WithTheme>
          <Card bordered>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ border: expect.any(String) });
    });

    it('applies custom border color', () => {
      const { container } = render(
        <WithTheme>
          <Card bordered borderColor="#ff0000">Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ borderColor: '#ff0000' });
    });

    it('renders square variant without border radius', () => {
      const { container } = render(
        <WithTheme>
          <Card square>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ borderRadius: '0' });
    });

    it('applies custom padding', () => {
      const { container } = render(
        <WithTheme>
          <Card padding={32}>Content</Card>
        </WithTheme>
      );
      const card = container.querySelector('div > div') as HTMLElement;
      expect(card).toHaveStyle({ padding: '32px' });
    });

    it('disables padding when specified', () => {
      const { container } = render(
        <WithTheme>
          <Card disablePadding>Content</Card>
        </WithTheme>
      );
      const card = container.querySelector('div > div') as HTMLElement;
      expect(card).not.toHaveStyle({ padding: expect.any(String) });
    });
  });

  describe('Interactions', () => {
    it('handles click events', () => {
      const handleClick = vi.fn();
      const { container } = render(
        <WithTheme>
          <Card onClick={handleClick}>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      card.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies hoverable styles', () => {
      const { container } = render(
        <WithTheme>
          <Card hoverable>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass(expect.stringContaining('css'));
    });
  });

  describe('Card Actions', () => {
    it('renders actions when provided', () => {
      render(
        <WithTheme>
          <Card
            actions={
              <>
                <button>Cancel</button>
                <button>Save</button>
              </>
            }
          >
            Content
          </Card>
        </WithTheme>
      );
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Save')).toBeInTheDocument();
    });

    it('does not render actions when not provided', () => {
      const { container } = render(
        <WithTheme>
          <Card>Content</Card>
        </WithTheme>
      );
      expect(container.querySelector('[class*="CardActions"]')).not.toBeInTheDocument();
    });
  });

  describe('Render Prop', () => {
    it('supports render prop function', () => {
      render(
        <WithTheme>
          <Card>{({ hovered }) => <span>{hovered ? 'Hovered' : 'Normal'}</span>}</Card>
        </WithTheme>
      );
      expect(screen.getByText('Normal')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('passes through ARIA attributes', () => {
      const { container } = render(
        <WithTheme>
          <Card role="article" aria-label="Test card">
            Content
          </Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveAttribute('role', 'article');
      expect(card).toHaveAttribute('aria-label', 'Test card');
    });

    it('applies custom className', () => {
      const { container } = render(
        <WithTheme>
          <Card className="custom-card">Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveClass('custom-card');
    });
  });

  describe('Custom Styling', () => {
    it('applies sx prop styles', () => {
      const { container } = render(
        <WithTheme>
          <Card sx={{ backgroundColor: 'red', color: 'white' }}>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ backgroundColor: 'red' });
      expect(card).toHaveStyle({ color: 'white' });
    });

    it('applies inline styles', () => {
      const { container } = render(
        <WithTheme>
          <Card style={{ margin: '16px' }}>Content</Card>
        </WithTheme>
      );
      const card = container.firstChild as HTMLElement;
      expect(card).toHaveStyle({ margin: '16px' });
    });
  });
});

describe('CardContent Component', () => {
  it('renders children correctly', () => {
    render(
      <WithTheme>
        <CardContent>
          <span>Content</span>
        </CardContent>
      </WithTheme>
    );
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('applies padding by default', () => {
    const { container } = render(
      <WithTheme>
        <CardContent>Content</CardContent>
      </WithTheme>
    );
    const content = container.firstChild as HTMLElement;
    expect(content).toHaveStyle({ padding: expect.any(String) });
  });

  it('disables padding when specified', () => {
    const { container } = render(
      <WithTheme>
        <CardContent disablePadding>Content</CardContent>
      </WithTheme>
    );
    const content = container.firstChild as HTMLElement;
    expect(content).not.toHaveStyle({ padding: expect.any(String) });
  });
});

describe('CardActions Component', () => {
  it('renders actions correctly', () => {
    render(
      <WithTheme>
        <CardActions>
          <button>Action 1</button>
          <button>Action 2</button>
        </CardActions>
      </WithTheme>
    );
    expect(screen.getByText('Action 1')).toBeInTheDocument();
    expect(screen.getByText('Action 2')).toBeInTheDocument();
  });

  it('applies divider styling', () => {
    const { container } = render(
      <WithTheme>
        <CardActions>
          <button>Action</button>
        </CardActions>
      </WithTheme>
    );
    const actions = container.firstChild as HTMLElement;
    expect(actions).toHaveStyle({ borderTop: expect.stringContaining('1px solid') });
  });
});

describe('CardHeader Component', () => {
  it('renders title', () => {
    render(
      <WithTheme>
        <CardHeader title="Card Title" />
      </WithTheme>
    );
    expect(screen.getByText('Card Title')).toBeInTheDocument();
  });

  it('renders subheader', () => {
    render(
      <WithTheme>
        <CardHeader title="Title" subheader="September 14, 2016" />
      </WithTheme>
    );
    expect(screen.getByText('September 14, 2016')).toBeInTheDocument();
  });

  it('renders avatar', () => {
    render(
      <WithTheme>
        <CardHeader title="Title" avatar={<span data-testid="avatar">AV</span>} />
      </WithTheme>
    );
    expect(screen.getByTestId('avatar')).toBeInTheDocument();
  });

  it('renders action', () => {
    render(
      <WithTheme>
        <CardHeader title="Title" action={<button data-testid="action">Action</button>} />
      </WithTheme>
    );
    expect(screen.getByTestId('action')).toBeInTheDocument();
  });

  it('disables padding when specified', () => {
    const { container } = render(
      <WithTheme>
        <CardHeader title="Title" disablePadding />
      </WithTheme>
    );
    const header = container.firstChild as HTMLElement;
    expect(header).toHaveStyle({ padding: '0' });
  });

  it('applies custom className', () => {
    const { container } = render(
      <WithTheme>
        <CardHeader title="Title" className="custom-header" />
      </WithTheme>
    );
    const header = container.firstChild as HTMLElement;
    expect(header).toHaveClass('custom-header');
  });
});

describe('Integration Tests', () => {
  it('renders complete card with all sub-components', () => {
    render(
      <WithTheme>
        <Card>
          <CardHeader title="Title" subheader="Subheader" />
          <CardContent>
            <p>Card content goes here...</p>
          </CardContent>
          <CardActions>
            <button>Cancel</button>
            <button>Save</button>
          </CardActions>
        </Card>
      </WithTheme>
    );
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Subheader')).toBeInTheDocument();
    expect(screen.getByText(/card content/i)).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('renders card with image', () => {
    const { container } = render(
      <WithTheme>
        <Card disablePadding>
          <img src="/test.jpg" alt="Test" style={{ width: '100%' }} />
          <CardContent>
            <p>Content below image</p>
          </CardContent>
        </Card>
      </WithTheme>
    );
    const img = container.querySelector('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', '/test.jpg');
  });

  it('renders interactive card with hover effect', () => {
    const handleClick = vi.fn();
    const { container } = render(
      <WithTheme>
        <Card hoverable onClick={handleClick}>
          <CardContent>
            <p>Hoverable card content</p>
          </CardContent>
        </Card>
      </WithTheme>
    );
    const card = container.firstChild as HTMLElement;
    card.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders outlined card with custom border', () => {
    render(
      <WithTheme>
        <Card outlined borderColor="#1976d2">
          <CardHeader title="Outlined Card" />
          <CardContent>
            <p>With custom border color</p>
          </CardContent>
        </Card>
      </WithTheme>
    );
    expect(screen.getByText('Outlined Card')).toBeInTheDocument();
    expect(screen.getByText(/with custom border/i)).toBeInTheDocument();
  });
});
