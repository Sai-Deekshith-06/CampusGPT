import { renderHook, act } from '@testing-library/react';
import { useFileProcessingEvents } from './useFileProcessingEvents';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('useFileProcessingEvents', () => {
  let mockEventSource;

  beforeEach(() => {
    mockEventSource = {
      addEventListener: vi.fn(),
      close: vi.fn(),
    };
    global.EventSource = vi.fn(function() { return mockEventSource; });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with file props', () => {
    const file = { processing_status: 'pending', processing_stage: 'unknown' };
    const { result } = renderHook(() => useFileProcessingEvents(file));
    
    expect(result.current.status).toBe('pending');
    expect(result.current.stage).toBe('unknown');
    expect(result.current.connectionState).toBe('idle'); // Connecting starts async
  });

  it('should not connect if terminal state', () => {
    const file = { campusgpt_job_id: '123', processing_status: 'completed' };
    renderHook(() => useFileProcessingEvents(file));
    expect(global.EventSource).not.toHaveBeenCalled();
  });

  it('should not connect if missing job id', () => {
    const file = { processing_status: 'pending' };
    renderHook(() => useFileProcessingEvents(file));
    expect(global.EventSource).not.toHaveBeenCalled();
  });

  it('should connect and handle processing events', () => {
    const file = { path: '/test.pdf', campusgpt_job_id: '123', processing_status: 'pending' };
    const { result } = renderHook(() => useFileProcessingEvents(file));
    
    expect(global.EventSource).toHaveBeenCalledWith(
      expect.stringContaining('processing-events?path=%2Ftest.pdf'),
      expect.any(Object)
    );

    const onOpen = mockEventSource.onopen;
    act(() => {
      if (onOpen) onOpen();
    });
    expect(result.current.connectionState).toBe('connected');

    const statusHandler = mockEventSource.addEventListener.mock.calls.find(c => c[0] === 'processing_status')[1];
    
    act(() => {
      statusHandler({ data: JSON.stringify({ status: 'running', stage: 'conversion' }) });
    });
    
    expect(result.current.status).toBe('running');
    expect(result.current.stage).toBe('conversion');
  });

  it('should close connection on terminal event', () => {
    const file = { path: '/test.pdf', campusgpt_job_id: '123', processing_status: 'pending' };
    const { result } = renderHook(() => useFileProcessingEvents(file));
    
    const statusHandler = mockEventSource.addEventListener.mock.calls.find(c => c[0] === 'processing_status')[1];
    
    act(() => {
      statusHandler({ data: JSON.stringify({ status: 'completed' }) });
    });
    
    expect(result.current.status).toBe('completed');
    expect(mockEventSource.close).toHaveBeenCalled();
    expect(result.current.connectionState).toBe('disconnected');
  });

  it('should handle malformed JSON', () => {
    const file = { path: '/test.pdf', campusgpt_job_id: '123', processing_status: 'pending' };
    const { result } = renderHook(() => useFileProcessingEvents(file));
    
    const statusHandler = mockEventSource.addEventListener.mock.calls.find(c => c[0] === 'processing_status')[1];
    
    act(() => {
      statusHandler({ data: 'invalid json {' });
    });
    
    // Should not crash, status remains pending
    expect(result.current.status).toBe('pending');
  });
});
