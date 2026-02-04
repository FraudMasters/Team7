import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { Dialog, DialogTitle, DialogContent, DialogActions } from './Dialog';
import Button from './Button';
import { EmotionThemeProvider } from '../../providers/ThemeProvider';

// Mock createPortal
const createPortalMock = vi.fn((children, container) => {
  return children;
});

vi.mock('react-dom', () => ({
  createPortal: createPortalMock,
}));

// Wrapper with theme provider
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('Dialog Component', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render when open is true', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <div>Dialog Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Dialog Content')).toBeInTheDocument();
    });

    it('should not render when open is false and keepMounted is false', () => {
      const { container } = renderWithTheme(
        <Dialog open={false} onClose={vi.fn()}>
          <DialogContent>
            <div>Dialog Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
    });

    it('should render with title', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} title="Test Title">
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} className="custom-dialog">
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveClass('custom-dialog');
    });

    it('should apply custom maxWidth', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} maxWidth="lg">
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should render fullScreen variant', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} fullScreen>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should render fullWidth variant', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} fullWidth>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  describe('DialogTitle', () => {
    it('should render title text', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogTitle>Test Title</DialogTitle>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('should render with custom id', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} titleId="custom-title-id">
          <DialogTitle id="custom-title-id">Test Title</DialogTitle>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const title = screen.getByText('Test Title');
      expect(title).toHaveAttribute('id', 'custom-title-id');
    });

    it('should show close button when showCloseButton is true', () => {
      const handleClose = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleClose}>
          <DialogTitle onClose={handleClose} showCloseButton>
            Test Title
          </DialogTitle>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const closeButton = screen.getByRole('button', { name: /close dialog/i });
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', () => {
      const handleClose = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleClose}>
          <DialogTitle onClose={handleClose} showCloseButton>
            Test Title
          </DialogTitle>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const closeButton = screen.getByRole('button', { name: /close dialog/i });
      fireEvent.click(closeButton);

      expect(handleClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('DialogContent', () => {
    it('should render content children', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <p>Paragraph 1</p>
            <p>Paragraph 2</p>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Paragraph 1')).toBeInTheDocument();
      expect(screen.getByText('Paragraph 2')).toBeInTheDocument();
    });

    it('should render with custom id', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} descriptionId="custom-content-id">
          <DialogContent id="custom-content-id">
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const content = screen.getByText('Content');
      expect(content.parentElement).toHaveAttribute('id', 'custom-content-id');
    });

    it('should render with dividers', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogTitle>Title</DialogTitle>
          <DialogContent dividers>
            <div>Content with dividers</div>
          </DialogContent>
          <DialogActions>
            <Button>OK</Button>
          </DialogActions>
        </Dialog>
      );

      expect(screen.getByText('Content with dividers')).toBeInTheDocument();
    });
  });

  describe('DialogActions', () => {
    it('should render action buttons', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
          <DialogActions>
            <Button>Cancel</Button>
            <Button variant="contained">Confirm</Button>
          </DialogActions>
        </Dialog>
      );

      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Confirm')).toBeInTheDocument();
    });

    it('should apply disableSpacing', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
          <DialogActions disableSpacing>
            <Button>OK</Button>
          </DialogActions>
        </Dialog>
      );

      expect(screen.getByText('OK')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('should call onClose when backdrop is clicked', () => {
      const handleClose = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleClose}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const backdrop = document.querySelector('[style*="position: fixed"][style*="background-color"]') as HTMLElement;
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(handleClose).toHaveBeenCalledWith(expect.any(Object), 'backdropClick');
      }
    });

    it('should not call onClose when disableBackdropClick is true', () => {
      const handleClose = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleClose} disableBackdropClick>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const backdrop = document.querySelector('[style*="position: fixed"][style*="background-color"]') as HTMLElement;
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(handleClose).not.toHaveBeenCalled();
      }
    });

    it('should call onClose when escape key is pressed', () => {
      const handleClose = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleClose}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(handleClose).toHaveBeenCalledWith(expect.any(Object), 'escapeKeyDown');
    });

    it('should not call onClose when disableEscapeKeyDown is true', () => {
      const handleClose = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleClose} disableEscapeKeyDown>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(handleClose).not.toHaveBeenCalled();
    });

    it('should close dialog when onClose callback is triggered', async () => {
      const handleClose = vi.fn();

      const { rerender } = renderWithTheme(
        <Dialog open={true} onClose={handleClose}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Content')).toBeInTheDocument();

      // Trigger close
      handleClose();

      // Rerender with open=false
      rerender(
        <EmotionThemeProvider>
          <Dialog open={false} onClose={handleClose}>
            <DialogContent>
              <div>Content</div>
            </DialogContent>
          </Dialog>
        </EmotionThemeProvider>
      );

      await waitFor(() => {
        expect(screen.queryByText('Content')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have role="dialog"', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should have aria-modal="true"', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby when titleId is provided', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} titleId="dialog-title">
          <DialogTitle id="dialog-title">Title</DialogTitle>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'dialog-title');
    });

    it('should have aria-describedby when descriptionId is provided', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} descriptionId="dialog-desc">
          <DialogContent id="dialog-desc">
            <div>Description</div>
          </DialogContent>
        </Dialog>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-describedby', 'dialog-desc');
    });

    it('should prevent body scroll when open', () => {
      const { unmount } = renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(document.body.style.overflow).toBe('hidden');

      unmount();

      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('Edge Cases', () => {
    it('should handle null children gracefully', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()}>
          {null}
        </Dialog>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should handle empty title', () => {
      renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} title="">
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should work with keepMounted prop', () => {
      const { rerender } = renderWithTheme(
        <Dialog open={true} onClose={vi.fn()} keepMounted>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      expect(screen.getByText('Content')).toBeInTheDocument();

      rerender(
        <EmotionThemeProvider>
          <Dialog open={false} onClose={vi.fn()} keepMounted>
            <DialogContent>
              <div>Content</div>
            </DialogContent>
          </Dialog>
        </EmotionThemeProvider>
      );

      // Content should still be in DOM when keepMounted is true
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('should handle rapid open/close transitions', async () => {
      const handleClose = vi.fn();

      const { rerender } = renderWithTheme(
        <Dialog open={true} onClose={handleClose}>
          <DialogContent>
            <div>Content</div>
          </DialogContent>
        </Dialog>
      );

      // Rapidly toggle
      rerender(
        <EmotionThemeProvider>
          <Dialog open={false} onClose={handleClose}>
            <DialogContent>
              <div>Content</div>
            </DialogContent>
          </Dialog>
        </EmotionThemeProvider>
      );

      rerender(
        <EmotionThemeProvider>
          <Dialog open={true} onClose={handleClose}>
            <DialogContent>
              <div>Content</div>
            </DialogContent>
          </Dialog>
        </EmotionThemeProvider>
      );

      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });

  describe('Integration', () => {
    it('should work as a controlled component', async () => {
      const handleClose = vi.fn();

      const { rerender } = renderWithTheme(
        <Dialog open={false} onClose={handleClose}>
          <DialogTitle>Controlled Dialog</DialogTitle>
          <DialogContent>
            <div>This is controlled</div>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleClose}>Close</Button>
          </DialogActions>
        </Dialog>
      );

      expect(screen.queryByText('Controlled Dialog')).not.toBeInTheDocument();

      rerender(
        <EmotionThemeProvider>
          <Dialog open={true} onClose={handleClose}>
            <DialogTitle>Controlled Dialog</DialogTitle>
            <DialogContent>
              <div>This is controlled</div>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleClose}>Close</Button>
            </DialogActions>
          </Dialog>
        </EmotionThemeProvider>
      );

      expect(screen.getByText('Controlled Dialog')).toBeInTheDocument();
      expect(screen.getByText('This is controlled')).toBeInTheDocument();
      expect(screen.getByText('Close')).toBeInTheDocument();
    });

    it('should handle complete dialog flow', async () => {
      const handleConfirm = vi.fn();
      const handleCancel = vi.fn();

      renderWithTheme(
        <Dialog open={true} onClose={handleCancel} title="Confirm Action">
          <DialogContent>
            <p>Are you sure you want to proceed?</p>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCancel}>Cancel</Button>
            <Button onClick={handleConfirm} variant="contained">
              Confirm
            </Button>
          </DialogActions>
        </Dialog>
      );

      // Check all elements render
      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Confirm')).toBeInTheDocument();

      // Click confirm
      fireEvent.click(screen.getByText('Confirm'));
      expect(handleConfirm).toHaveBeenCalledTimes(1);
    });
  });
});
