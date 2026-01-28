import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { ToastProvider, useToast, ToastType } from './ToastContext';

// Test component to trigger toasts
const ToastTrigger = ({ type, message, description }: { type: ToastType; message: string; description?: string }) => {
  const toast = useToast();

  const handleClick = () => {
    if (type === 'success') toast.success(message, description);
    else if (type === 'error') toast.error(message, description);
    else if (type === 'warning') toast.warning(message, description);
    else if (type === 'info') toast.info(message, description);
    else if (type === 'delete') toast.deleted(message, description);
  };

  return <button onClick={handleClick}>Show Toast</button>;
};

describe('ToastContext', () => {
  it('should throw error when useToast is used outside provider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<ToastTrigger type="success" message="Test" />);
    }).toThrow('useToast must be used within a ToastProvider');

    consoleError.mockRestore();
  });

  it('should show success toast', async () => {
    render(
      <ToastProvider>
        <ToastTrigger type="success" message="Success message" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    await waitFor(() => {
      expect(screen.getByText('Success message')).toBeInTheDocument();
    });
  });

  it('should show error toast', async () => {
    render(
      <ToastProvider>
        <ToastTrigger type="error" message="Error message" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    await waitFor(() => {
      expect(screen.getByText('Error message')).toBeInTheDocument();
    });
  });

  it('should show warning toast', async () => {
    render(
      <ToastProvider>
        <ToastTrigger type="warning" message="Warning message" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    await waitFor(() => {
      expect(screen.getByText('Warning message')).toBeInTheDocument();
    });
  });

  it('should show info toast', async () => {
    render(
      <ToastProvider>
        <ToastTrigger type="info" message="Info message" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    await waitFor(() => {
      expect(screen.getByText('Info message')).toBeInTheDocument();
    });
  });

  it('should show toast with description', async () => {
    render(
      <ToastProvider>
        <ToastTrigger type="success" message="Main message" description="Detailed description" />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show Toast'));

    await waitFor(() => {
      expect(screen.getByText('Main message')).toBeInTheDocument();
      expect(screen.getByText('Detailed description')).toBeInTheDocument();
    });
  });

  it('should show multiple toasts', async () => {
    const MultiToastTrigger = () => {
      const toast = useToast();
      return (
        <>
          <button onClick={() => toast.success('Toast One')}>Show First</button>
          <button onClick={() => toast.error('Toast Two')}>Show Second</button>
        </>
      );
    };

    render(
      <ToastProvider>
        <MultiToastTrigger />
      </ToastProvider>
    );

    fireEvent.click(screen.getByText('Show First'));
    fireEvent.click(screen.getByText('Show Second'));

    await waitFor(() => {
      expect(screen.getByText('Toast One')).toBeInTheDocument();
      expect(screen.getByText('Toast Two')).toBeInTheDocument();
    });
  });
});
