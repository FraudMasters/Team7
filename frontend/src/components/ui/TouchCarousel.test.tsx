/**
 * TouchCarousel Component Tests
 *
 * Basic smoke tests to verify the component can be imported and renders.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TouchCarousel, { TouchCarouselProps } from './TouchCarousel';

// Mock the useSwipeGesture hook
jest.mock('../../hooks/useSwipeGesture', () => ({
  useSwipeGesture: jest.fn(() => ({
    ref: jest.fn(),
  })),
}));

describe('TouchCarousel Component', () => {
  it('should import without errors', () => {
    expect(TouchCarousel).toBeDefined();
  });

  it('should render children correctly', () => {
    render(
      <TouchCarousel>
        <div>Card 1</div>
        <div>Card 2</div>
        <div>Card 3</div>
      </TouchCarousel>
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.getByText('Card 2')).toBeInTheDocument();
    expect(screen.getByText('Card 3')).toBeInTheDocument();
  });

  it('should render with empty array message', () => {
    render(
      <TouchCarousel>
        {[]}
      </TouchCarousel>
    );

    expect(screen.getByText('No items to display')).toBeInTheDocument();
  });

  it('should show navigation dots by default', () => {
    render(
      <TouchCarousel showDots={true}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    // MobileStepper should be rendered
    const stepper = document.querySelector('.MuiMobileStepper-root');
    expect(stepper).toBeInTheDocument();
  });

  it('should hide navigation dots when showDots is false', () => {
    render(
      <TouchCarousel showDots={false}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    const stepper = document.querySelector('.MuiMobileStepper-root');
    expect(stepper).not.toBeInTheDocument();
  });

  it('should hide arrows on mobile by default', () => {
    // Mock window.innerWidth to be mobile size
    global.innerWidth = 375;

    render(
      <TouchCarousel showArrows={true}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    // Arrows should have display: none on mobile (xs breakpoint)
    const arrows = document.querySelectorAll('button[aria-label="Previous item"], button[aria-label="Next item"]');
    arrows.forEach((arrow) => {
      expect(arrow).not.toBeVisible();
    });
  });

  it('should render with custom height', () => {
    render(
      <TouchCarousel height={400}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    const container = screen.getByText('Card 1').closest('.MuiBox-root');
    expect(container).toHaveStyle({ height: '400px' });
  });

  it('should render with custom sx styles', () => {
    render(
      <TouchCarousel sx={{ bgcolor: 'red', maxHeight: 500 }}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    const container = screen.getByText('Card 1').closest('.MuiBox-root');
    expect(container).toHaveStyle({ maxHeight: 500 });
  });

  it('should handle single item', () => {
    render(
      <TouchCarousel>
        <div>Single Card</div>
      </TouchCarousel>
    );

    expect(screen.getByText('Single Card')).toBeInTheDocument();

    // No dots should be shown for single item
    const stepper = document.querySelector('.MuiMobileStepper-root');
    expect(stepper).not.toBeInTheDocument();
  });

  it('should have swipe hint on mobile', () => {
    render(
      <TouchCarousel enableSwipe={true}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    // Swipe hint should be present
    expect(screen.getByText(/Swipe/)).toBeInTheDocument();
  });

  it('should not have swipe hint when swipe is disabled', () => {
    render(
      <TouchCarousel enableSwipe={false}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    expect(screen.queryByText(/Swipe/)).not.toBeInTheDocument();
  });

  it('should handle infinite mode', () => {
    const onChange = jest.fn();

    render(
      <TouchCarousel infinite={true} onChange={onChange}>
        <div>Card 1</div>
        <div>Card 2</div>
        <div>Card 3</div>
      </TouchCarousel>
    );

    // Component should render without errors
    expect(screen.getByText('Card 1')).toBeInTheDocument();
  });

  it('should handle non-infinite mode', () => {
    render(
      <TouchCarousel infinite={false}>
        <div>Card 1</div>
        <div>Card 2</div>
        <div>Card 3</div>
      </TouchCarousel>
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
  });

  it('should render with autoPlay enabled', () => {
    jest.useFakeTimers();

    render(
      <TouchCarousel autoPlay={true} autoPlayInterval={3000}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();

    jest.useRealTimers();
  });

  it('should pass custom callbacks', () => {
    const onChange = jest.fn();
    const onNext = jest.fn();
    const onPrevious = jest.fn();

    render(
      <TouchCarousel
        onChange={onChange}
        onNext={onNext}
        onPrevious={onPrevious}
      >
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
  });

  it('should respect enableTouchAction prop', () => {
    render(
      <TouchCarousel enableTouchAction={false}>
        <div>Card 1</div>
        <div>Card 2</div>
      </TouchCarousel>
    );

    expect(screen.getByText('Card 1')).toBeInTheDocument();
  });

  it('should handle children array correctly', () => {
    const cards = [
      <div key="1">Card 1</div>,
      <div key="2">Card 2</div>,
      <div key="3">Card 3</div>,
    ];

    render(<TouchCarousel>{cards}</TouchCarousel>);

    expect(screen.getByText('Card 1')).toBeInTheDocument();
    expect(screen.getByText('Card 2')).toBeInTheDocument();
    expect(screen.getByText('Card 3')).toBeInTheDocument();
  });

  it('should render with React elements as children', () => {
    const cardElement = <div data-testid="custom-card">Custom Card</div>;

    render(
      <TouchCarousel>
        {cardElement}
        <div>Another Card</div>
      </TouchCarousel>
    );

    expect(screen.getByTestId('custom-card')).toBeInTheDocument();
    expect(screen.getByText('Another Card')).toBeInTheDocument();
  });
});
