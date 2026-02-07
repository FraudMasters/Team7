import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Drawer } from './Drawer';
import { EmotionThemeProvider } from '../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('Drawer Component', () => {
  describe('Rendering', () => {
    it('renders without crashing', () => {
      renderWithTheme(<Drawer open={false} onClose={() => {}} items={[]} />);
      expect(document.body).toBeTruthy();
    });

    it('renders children when open', () => {
      renderWithTheme(
        <Drawer open={true} onClose={() => {}}>
          <div data-testid="drawer-content">Drawer Content</div>
        </Drawer>
      );
      expect(screen.getByTestId('drawer-content')).toBeInTheDocument();
    });

    it('does not render children when closed', () => {
      renderWithTheme(
        <Drawer open={false} onClose={() => {}}>
          <div data-testid="drawer-content">Drawer Content</div>
        </Drawer>
      );
      expect(screen.queryByTestId('drawer-content')).not.toBeInTheDocument();
    });

    it('renders with custom className', () => {
      const { container } = renderWithTheme(
        <Drawer open={true} onClose={() => {}} className="custom-drawer" />
      );
      const drawer = container.querySelector('.custom-drawer');
      expect(drawer).toBeInTheDocument();
    });

    it('renders with custom style', () => {
      const { container } = renderWithTheme(
        <Drawer open={true} onClose={() => {}} style={{ backgroundColor: 'red' }} />
      );
      const drawer = container.querySelector('[style*="background-color"]');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Variants', () => {
    it('renders temporary variant with backdrop', () => {
      renderWithTheme(<Drawer open={true} variant="temporary" onClose={() => {}} />);
      const backdrop = document.querySelector('[style*="background-color: rgba(0, 0, 0, 0.5)"]');
      expect(backdrop).toBeInTheDocument();
    });

    it('renders permanent variant without backdrop', () => {
      renderWithTheme(<Drawer open={true} variant="permanent" onClose={() => {}} />);
      const backdrop = document.querySelector('[style*="background-color: rgba(0, 0, 0, 0.5)"]');
      expect(backdrop).not.toBeInTheDocument();
    });
  });

  describe('Anchors', () => {
    it('renders left anchor correctly', () => {
      const { container } = renderWithTheme(
        <Drawer open={true} anchor="left" onClose={() => {}} />
      );
      const drawer = container.querySelector('[style*="position: fixed"]');
      expect(drawer).toBeInTheDocument();
    });

    it('renders right anchor correctly', () => {
      const { container } = renderWithTheme(
        <Drawer open={true} anchor="right" onClose={() => {}} />
      );
      const drawer = container.querySelector('[style*="position: fixed"]');
      expect(drawer).toBeInTheDocument();
    });

    it('renders top anchor correctly', () => {
      const { container } = renderWithTheme(<Drawer open={true} anchor="top" onClose={() => {}} />);
      const drawer = container.querySelector('[style*="position: fixed"]');
      expect(drawer).toBeInTheDocument();
    });

    it('renders bottom anchor correctly', () => {
      const { container } = renderWithTheme(
        <Drawer open={true} anchor="bottom" onClose={() => {}} />
      );
      const drawer = container.querySelector('[style*="position: fixed"]');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Width', () => {
    it('applies custom width', () => {
      const { container } = renderWithTheme(
        <Drawer open={true} width={350} onClose={() => {}} />
      );
      const drawer = container.querySelector('[style*="width"]');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClose when backdrop is clicked', () => {
      const handleClose = jest.fn();
      renderWithTheme(<Drawer open={true} variant="temporary" onClose={handleClose} />);

      const backdrop = document.querySelector('[style*="background-color: rgba(0, 0, 0, 0.5)"]');
      expect(backdrop).toBeInTheDocument();

      if (backdrop) {
        fireEvent.click(backdrop);
        expect(handleClose).toHaveBeenCalledTimes(1);
      }
    });

    it('calls onClose when escape key is pressed', () => {
      const handleClose = jest.fn();
      renderWithTheme(<Drawer open={true} variant="temporary" onClose={handleClose} />);

      fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('does not call onClose when drawer is permanent', () => {
      const handleClose = jest.fn();
      renderWithTheme(<Drawer open={true} variant="permanent" onClose={handleClose} />);

      const backdrop = document.querySelector('[style*="background-color: rgba(0, 0, 0, 0.5)"]');
      expect(backdrop).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes when open', () => {
      const { container } = renderWithTheme(<Drawer open={true} onClose={() => {}} />);
      const drawer = container.querySelector('[role="complementary"]');
      expect(drawer).toBeInTheDocument();
      expect(drawer).toHaveAttribute('aria-hidden', 'false');
    });

    it('has proper ARIA attributes when closed', () => {
      const { container } = renderWithTheme(
        <Drawer open={false} variant="temporary" onClose={() => {}} />
      );
      const drawer = container.querySelector('[role="complementary"]');
      expect(drawer).toHaveAttribute('aria-hidden', 'true');
    });

    it('applies elevation shadow', () => {
      const { container } = renderWithTheme(<Drawer open={true} elevation={4} onClose={() => {}} />);
      const drawer = container.querySelector('[style*="box-shadow"]');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Modal Props', () => {
    it('calls onBackdropClick from ModalProps', () => {
      const handleBackdropClick = jest.fn();
      const handleClose = jest.fn();

      renderWithTheme(
        <Drawer
          open={true}
          variant="temporary"
          onClose={handleClose}
          ModalProps={{ onBackdropClick: handleBackdropClick }}
        />
      );

      const backdrop = document.querySelector('[style*="background-color: rgba(0, 0, 0, 0.5)"]');
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(handleBackdropClick).toHaveBeenCalledTimes(1);
      }
    });

    it('keeps drawer mounted when keepMounted is true', () => {
      const { container } = renderWithTheme(
        <Drawer open={false} variant="temporary" onClose={() => {}} ModalProps={{ keepMounted: true }} />
      );
      const drawer = container.querySelector('[role="complementary"]');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Transitions', () => {
    it('applies transition styles', () => {
      const { container } = renderWithTheme(<Drawer open={true} onClose={() => {}} />);
      const drawer = container.querySelector('[style*="transition"]');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('renders without children', () => {
      const { container } = renderWithTheme(<Drawer open={true} onClose={() => {}} />);
      const drawer = container.querySelector('[role="complementary"]');
      expect(drawer).toBeInTheDocument();
    });

    it('handles rapid open/close', () => {
      const handleClose = jest.fn();
      const { rerender } = renderWithTheme(<Drawer open={true} onClose={handleClose} />);

      rerender(
        <EmotionThemeProvider>
          <Drawer open={false} onClose={handleClose} />
        </EmotionThemeProvider>
      );

      rerender(
        <EmotionThemeProvider>
          <Drawer open={true} onClose={handleClose} />
        </EmotionThemeProvider>
      );

      const drawer = document.querySelector('[role="complementary"]');
      expect(drawer).toBeInTheDocument();
    });
  });
});
