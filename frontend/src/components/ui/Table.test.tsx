import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  Table,
  TableHead,
  TableBody,
  TableFooter,
  TableRow,
  TableCell,
} from './Table';
import { EmotionThemeProvider } from '../providers/ThemeProvider';

/**
 * Helper to render with theme provider
 */
const renderWithTheme = (component: React.ReactElement) => {
  return render(<EmotionThemeProvider>{component}</EmotionThemeProvider>);
};

describe('Table Components', () => {
  describe('Table', () => {
    it('renders without crashing', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      renderWithTheme(
        <Table className="custom-table">
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toHaveClass('custom-table');
    });

    it('renders with sticky header when stickyHeader is true', () => {
      renderWithTheme(
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Header</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('TableHead', () => {
    it('renders without crashing', () => {
      renderWithTheme(
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Header</TableCell>
            </TableRow>
          </TableHead>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      renderWithTheme(
        <Table>
          <TableHead className="custom-head">
            <TableRow>
              <TableCell>Header</TableCell>
            </TableRow>
          </TableHead>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('TableBody', () => {
    it('renders without crashing', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders multiple rows', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Row 1</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Row 2</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('Row 1')).toBeInTheDocument();
      expect(screen.getByText('Row 2')).toBeInTheDocument();
    });
  });

  describe('TableFooter', () => {
    it('renders without crashing', () => {
      renderWithTheme(
        <Table>
          <TableFooter>
            <TableRow>
              <TableCell>Footer</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('TableRow', () => {
    it('renders without crashing', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders with hover prop', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow hover>
              <TableCell>Hoverable</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders with selected prop', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow selected>
              <TableCell>Selected</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('handles onClick', () => {
      const handleClick = jest.fn();
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow onClick={handleClick}>
              <TableCell>Clickable</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      const row = screen.getByText('Clickable').closest('tr');
      row?.click();
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('TableCell', () => {
    it('renders without crashing', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('renders with different alignments', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell align="left">Left</TableCell>
              <TableCell align="center">Center</TableCell>
              <TableCell align="right">Right</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Left')).toBeInTheDocument();
      expect(screen.getByText('Center')).toBeInTheDocument();
      expect(screen.getByText('Right')).toBeInTheDocument();
    });

    it('renders with padding variants', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell padding="none">None</TableCell>
              <TableCell padding="normal">Normal</TableCell>
              <TableCell padding="checkbox">Checkbox</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('None')).toBeInTheDocument();
      expect(screen.getByText('Normal')).toBeInTheDocument();
      expect(screen.getByText('Checkbox')).toBeInTheDocument();
    });

    it('renders with variant', () => {
      renderWithTheme(
        <Table>
          <TableHead>
            <TableRow>
              <TableCell variant="head">Header</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell variant="body">Body</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Header')).toBeInTheDocument();
      expect(screen.getByText('Body')).toBeInTheDocument();
    });

    it('renders with scope for header cells', () => {
      renderWithTheme(
        <Table>
          <TableHead>
            <TableRow>
              <TableCell component="th" scope="col">
                Column Header
              </TableCell>
            </TableRow>
          </TableHead>
        </Table>
      );
      expect(screen.getByText('Column Header')).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className="custom-cell">Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Content')).toHaveClass('custom-cell');
    });

    it('renders with custom style', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell style={{ color: 'red' }}>Styled</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      const cell = screen.getByText('Styled');
      expect(cell).toHaveStyle({ color: 'red' });
    });
  });

  describe('Integration Tests', () => {
    it('renders a complete table with all components', () => {
      renderWithTheme(
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell align="right">Age</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow hover>
              <TableCell>John Doe</TableCell>
              <TableCell align="right">30</TableCell>
              <TableCell align="right">$100</TableCell>
            </TableRow>
            <TableRow selected>
              <TableCell>Jane Smith</TableCell>
              <TableCell align="right">25</TableCell>
              <TableCell align="right">$200</TableCell>
            </TableRow>
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell>Total</TableCell>
              <TableCell />
              <TableCell align="right">$300</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      );

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Total')).toBeInTheDocument();
    });

    it('renders clickable rows', () => {
      const handleClick1 = jest.fn();
      const handleClick2 = jest.fn();

      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow onClick={handleClick1}>
              <TableCell>Row 1</TableCell>
            </TableRow>
            <TableRow onClick={handleClick2}>
              <TableCell>Row 2</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );

      const row1 = screen.getByText('Row 1').closest('tr');
      const row2 = screen.getByText('Row 2').closest('tr');

      row1?.click();
      row2?.click();

      expect(handleClick1).toHaveBeenCalledTimes(1);
      expect(handleClick2).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    it('renders table without body', () => {
      renderWithTheme(
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Header Only</TableCell>
            </TableRow>
          </TableHead>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders empty table body', () => {
      renderWithTheme(
        <Table>
          <TableBody />
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('renders row without cells', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow />
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('preserves custom data attributes', () => {
      renderWithTheme(
        <Table>
          <TableBody>
            <TableRow data-testid="custom-row">
              <TableCell data-value="test">Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByTestId('custom-row')).toBeInTheDocument();
      expect(screen.getByText('Cell')).toHaveAttribute('data-value', 'test');
    });
  });
});
