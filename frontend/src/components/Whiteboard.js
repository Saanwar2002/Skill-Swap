import React, { useEffect, useRef, useState, useCallback } from 'react';
import { fabric } from 'fabric';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import {
  PencilIcon,
  PaintBrushIcon,
  Square3Stack3DIcon,
  XMarkIcon,
  TrashIcon,
  ArrowUturnLeftIcon,
  ArrowUturnRightIcon,
  DocumentArrowDownIcon,
  PhotoIcon,
  ChatBubbleBottomCenterTextIcon,
  EyeSlashIcon,
  EyeIcon,
  CloudIcon
} from '@heroicons/react/24/outline';

const Whiteboard = ({ 
  sessionId, 
  isVisible, 
  onToggleVisibility, 
  onWhiteboardEvent,
  remoteEvents = []
}) => {
  const canvasRef = useRef(null);
  const fabricCanvasRef = useRef(null);
  const [selectedTool, setSelectedTool] = useState('pen');
  const [brushSize, setBrushSize] = useState(2);
  const [brushColor, setBrushColor] = useState('#000000');
  const [isDrawing, setIsDrawing] = useState(false);
  const [canvasHistory, setCanvasHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Tool configurations
  const tools = {
    pen: { cursor: 'crosshair', mode: 'drawing' },
    eraser: { cursor: 'crosshair', mode: 'eraser' },
    rectangle: { cursor: 'crosshair', mode: 'rectangle' },
    circle: { cursor: 'crosshair', mode: 'circle' },
    line: { cursor: 'crosshair', mode: 'line' },
    text: { cursor: 'text', mode: 'text' },
    select: { cursor: 'default', mode: 'selection' }
  };

  // Initialize Fabric.js canvas
  useEffect(() => {
    if (!canvasRef.current || fabricCanvasRef.current) return;

    const canvas = new fabric.Canvas(canvasRef.current, {
      width: 800,
      height: 600,
      backgroundColor: '#ffffff',
      selection: selectedTool === 'select',
      isDrawingMode: selectedTool === 'pen'
    });

    // Configure drawing brush
    canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
    canvas.freeDrawingBrush.width = brushSize;
    canvas.freeDrawingBrush.color = brushColor;

    // Event listeners
    canvas.on('path:created', handlePathCreated);
    canvas.on('object:added', handleObjectAdded);
    canvas.on('object:modified', handleObjectModified);
    canvas.on('selection:created', handleSelection);
    canvas.on('selection:updated', handleSelection);

    fabricCanvasRef.current = canvas;
    saveCanvasState();

    return () => {
      if (fabricCanvasRef.current) {
        fabricCanvasRef.current.dispose();
        fabricCanvasRef.current = null;
      }
    };
  }, []);

  // Handle tool changes
  useEffect(() => {
    if (!fabricCanvasRef.current) return;

    const canvas = fabricCanvasRef.current;
    canvas.isDrawingMode = selectedTool === 'pen';
    canvas.selection = selectedTool === 'select';

    // Configure cursor
    canvas.defaultCursor = tools[selectedTool]?.cursor || 'default';
    canvas.hoverCursor = tools[selectedTool]?.cursor || 'default';
    canvas.moveCursor = selectedTool === 'select' ? 'move' : tools[selectedTool]?.cursor || 'default';

    // Configure eraser mode
    if (selectedTool === 'eraser') {
      canvas.freeDrawingBrush = new fabric.EraserBrush(canvas);
      canvas.freeDrawingBrush.width = brushSize * 2;
      canvas.isDrawingMode = true;
    } else if (selectedTool === 'pen') {
      canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
      canvas.freeDrawingBrush.width = brushSize;
      canvas.freeDrawingBrush.color = brushColor;
    }
  }, [selectedTool, brushSize, brushColor]);

  // Handle remote events from other users
  useEffect(() => {
    if (!fabricCanvasRef.current || !remoteEvents.length) return;

    remoteEvents.forEach(event => {
      handleRemoteEvent(event);
    });
  }, [remoteEvents]);

  // Event handlers
  const handlePathCreated = useCallback((e) => {
    const pathData = e.path.toObject();
    const event = {
      type: 'path:created',
      data: { ...pathData, id: uuidv4() },
      timestamp: Date.now(),
      userId: 'current-user' // This will be replaced with actual user ID
    };
    
    onWhiteboardEvent?.(event);
    saveCanvasState();
  }, [onWhiteboardEvent]);

  const handleObjectAdded = useCallback((e) => {
    if (e.target.type !== 'path') {
      const objectData = e.target.toObject();
      const event = {
        type: 'object:added',
        data: { ...objectData, id: uuidv4() },
        timestamp: Date.now(),
        userId: 'current-user'
      };
      
      onWhiteboardEvent?.(event);
      saveCanvasState();
    }
  }, [onWhiteboardEvent]);

  const handleObjectModified = useCallback((e) => {
    const objectData = e.target.toObject();
    const event = {
      type: 'object:modified',
      data: objectData,
      timestamp: Date.now(),
      userId: 'current-user'
    };
    
    onWhiteboardEvent?.(event);
    saveCanvasState();
  }, [onWhiteboardEvent]);

  const handleSelection = useCallback(() => {
    saveCanvasState();
  }, []);

  const handleRemoteEvent = useCallback((event) => {
    if (!fabricCanvasRef.current) return;

    const canvas = fabricCanvasRef.current;
    
    switch (event.type) {
      case 'path:created':
        fabric.Path.fromObject(event.data, (path) => {
          canvas.add(path);
          canvas.renderAll();
        });
        break;
      
      case 'object:added':
        fabric.util.enlivenObjects([event.data], (objects) => {
          objects.forEach(obj => {
            canvas.add(obj);
          });
          canvas.renderAll();
        });
        break;
      
      case 'object:modified':
        const existingObject = canvas.getObjects().find(obj => obj.id === event.data.id);
        if (existingObject) {
          existingObject.set(event.data);
          canvas.renderAll();
        }
        break;
      
      case 'canvas:cleared':
        canvas.clear();
        canvas.setBackgroundColor('#ffffff', canvas.renderAll.bind(canvas));
        break;
      
      default:
        console.log('Unknown whiteboard event:', event.type);
    }
  }, []);

  // Canvas state management
  const saveCanvasState = useCallback(() => {
    if (!fabricCanvasRef.current) return;
    
    const state = JSON.stringify(fabricCanvasRef.current.toJSON());
    setCanvasHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(state);
      return newHistory.slice(-50); // Keep last 50 states
    });
    setHistoryIndex(prev => Math.min(prev + 1, 49));
  }, [historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex > 0 && fabricCanvasRef.current) {
      const newIndex = historyIndex - 1;
      const state = canvasHistory[newIndex];
      
      fabricCanvasRef.current.loadFromJSON(state, () => {
        fabricCanvasRef.current.renderAll();
        setHistoryIndex(newIndex);
      });

      const event = {
        type: 'canvas:undo',
        data: { state },
        timestamp: Date.now(),
        userId: 'current-user'
      };
      onWhiteboardEvent?.(event);
    }
  }, [historyIndex, canvasHistory, onWhiteboardEvent]);

  const redo = useCallback(() => {
    if (historyIndex < canvasHistory.length - 1 && fabricCanvasRef.current) {
      const newIndex = historyIndex + 1;
      const state = canvasHistory[newIndex];
      
      fabricCanvasRef.current.loadFromJSON(state, () => {
        fabricCanvasRef.current.renderAll();
        setHistoryIndex(newIndex);
      });

      const event = {
        type: 'canvas:redo',
        data: { state },
        timestamp: Date.now(),
        userId: 'current-user'
      };
      onWhiteboardEvent?.(event);
    }
  }, [historyIndex, canvasHistory, onWhiteboardEvent]);

  const clearCanvas = useCallback(() => {
    if (fabricCanvasRef.current) {
      fabricCanvasRef.current.clear();
      fabricCanvasRef.current.setBackgroundColor('#ffffff', fabricCanvasRef.current.renderAll.bind(fabricCanvasRef.current));
      
      const event = {
        type: 'canvas:cleared',
        data: {},
        timestamp: Date.now(),
        userId: 'current-user'
      };
      onWhiteboardEvent?.(event);
      saveCanvasState();
    }
  }, [onWhiteboardEvent, saveCanvasState]);

  const addText = useCallback(() => {
    if (!fabricCanvasRef.current) return;

    const text = new fabric.IText('Double click to edit', {
      left: 100,
      top: 100,
      fontSize: 20,
      fill: brushColor,
      fontFamily: 'Arial'
    });

    fabricCanvasRef.current.add(text);
    fabricCanvasRef.current.setActiveObject(text);
    text.enterEditing();
  }, [brushColor]);

  const addShape = useCallback((shapeType) => {
    if (!fabricCanvasRef.current) return;

    let shape;
    const commonProps = {
      left: 200,
      top: 200,
      fill: 'transparent',
      stroke: brushColor,
      strokeWidth: brushSize
    };

    switch (shapeType) {
      case 'rectangle':
        shape = new fabric.Rect({ ...commonProps, width: 100, height: 60 });
        break;
      case 'circle':
        shape = new fabric.Circle({ ...commonProps, radius: 50 });
        break;
      case 'line':
        shape = new fabric.Line([0, 0, 100, 0], { 
          ...commonProps, 
          fill: '', 
          strokeWidth: brushSize 
        });
        break;
      default:
        return;
    }

    fabricCanvasRef.current.add(shape);
    fabricCanvasRef.current.setActiveObject(shape);
  }, [brushColor, brushSize]);

  const exportCanvas = useCallback(() => {
    if (!fabricCanvasRef.current) return;

    const dataURL = fabricCanvasRef.current.toDataURL({
      format: 'png',
      quality: 1,
      multiplier: 2
    });

    const link = document.createElement('a');
    link.download = `whiteboard-${sessionId}-${Date.now()}.png`;
    link.href = dataURL;
    link.click();
  }, [sessionId]);

  const deleteSelected = useCallback(() => {
    if (fabricCanvasRef.current) {
      const activeObjects = fabricCanvasRef.current.getActiveObjects();
      fabricCanvasRef.current.discardActiveObject();
      fabricCanvasRef.current.remove(...activeObjects);
      saveCanvasState();
    }
  }, [saveCanvasState]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 z-40 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900">Interactive Whiteboard</h3>
          <div className="text-sm text-gray-500">Session: {sessionId}</div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleVisibility}
            className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
            title="Hide whiteboard"
          >
            <EyeSlashIcon className="h-5 w-5 text-gray-600" />
          </button>
          <button
            onClick={() => onToggleVisibility()}
            className="p-2 rounded-lg bg-red-100 hover:bg-red-200 text-red-600 transition-colors"
            title="Close whiteboard"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="bg-gray-50 border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Drawing Tools */}
            <div className="flex items-center space-x-1 bg-white rounded-lg p-1 border">
              {Object.entries(tools).map(([tool, config]) => (
                <button
                  key={tool}
                  onClick={() => setSelectedTool(tool)}
                  className={`p-2 rounded transition-colors ${
                    selectedTool === tool 
                      ? 'bg-blue-500 text-white' 
                      : 'hover:bg-gray-100 text-gray-600'
                  }`}
                  title={tool.charAt(0).toUpperCase() + tool.slice(1)}
                >
                  {tool === 'pen' && <PencilIcon className="h-4 w-4" />}
                  {tool === 'eraser' && <PaintBrushIcon className="h-4 w-4" />}
                  {tool === 'rectangle' && <Square3Stack3DIcon className="h-4 w-4" />}
                  {tool === 'circle' && <div className="w-4 h-4 border-2 border-current rounded-full" />}
                  {tool === 'line' && <div className="w-4 h-0 border-t-2 border-current" />}
                  {tool === 'text' && <ChatBubbleBottomCenterTextIcon className="h-4 w-4" />}
                  {tool === 'select' && <div className="w-4 h-4 border border-current" />}
                </button>
              ))}
            </div>

            {/* Shape Quick Access */}
            <div className="flex items-center space-x-1">
              <button
                onClick={() => addShape('rectangle')}
                className="p-2 rounded hover:bg-gray-100 text-gray-600"
                title="Add Rectangle"
              >
                <Square3Stack3DIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => addShape('circle')}
                className="p-2 rounded hover:bg-gray-100 text-gray-600"
                title="Add Circle"
              >
                <div className="w-4 h-4 border-2 border-current rounded-full" />
              </button>
              <button
                onClick={addText}
                className="p-2 rounded hover:bg-gray-100 text-gray-600"
                title="Add Text"
              >
                <ChatBubbleBottomCenterTextIcon className="h-4 w-4" />
              </button>
            </div>

            {/* Color and Size Controls */}
            <div className="flex items-center space-x-2 ml-4">
              <input
                type="color"
                value={brushColor}
                onChange={(e) => setBrushColor(e.target.value)}
                className="w-8 h-8 rounded border-2 border-gray-300 cursor-pointer"
                title="Brush Color"
              />
              <div className="flex items-center space-x-1">
                <label className="text-sm text-gray-600">Size:</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={brushSize}
                  onChange={(e) => setBrushSize(parseInt(e.target.value))}
                  className="w-20"
                />
                <span className="text-sm text-gray-600 w-6">{brushSize}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600"
              title="Undo"
            >
              <ArrowUturnLeftIcon className="h-4 w-4" />
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= canvasHistory.length - 1}
              className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed text-gray-600"
              title="Redo"
            >
              <ArrowUturnRightIcon className="h-4 w-4" />
            </button>
            <button
              onClick={deleteSelected}
              className="p-2 rounded hover:bg-red-100 text-red-600"
              title="Delete Selected"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
            <button
              onClick={clearCanvas}
              className="px-3 py-1 rounded bg-red-100 hover:bg-red-200 text-red-600 text-sm"
              title="Clear Canvas"
            >
              Clear All
            </button>
            <button
              onClick={exportCanvas}
              className="p-2 rounded hover:bg-green-100 text-green-600"
              title="Export Canvas"
            >
              <DocumentArrowDownIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 flex items-center justify-center bg-gray-100 p-4">
        <div className="bg-white rounded-lg shadow-lg">
          <canvas
            ref={canvasRef}
            className="border border-gray-200 rounded-lg"
          />
        </div>
      </div>

      {/* Status Bar */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <div>
            Tool: {selectedTool.charAt(0).toUpperCase() + selectedTool.slice(1)} | 
            Color: {brushColor} | 
            Size: {brushSize}px
          </div>
          <div>
            History: {historyIndex + 1}/{canvasHistory.length} | 
            Canvas: 800x600
          </div>
        </div>
      </div>
    </div>
  );
};

export default Whiteboard;