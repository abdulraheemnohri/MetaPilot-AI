"""
MetaPilot AI - UI Store

UI-related state that doesn't belong in other stores.
"""

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface ModalState {
  isOpen: boolean;
  type: string | null;
  data?: any;
}

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
  createdAt: number;
}

interface ConfirmationDialog {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

interface UiState {
  // Modals
  modals: ModalState[];
  
  // Toasts
  toasts: Toast[];
  
  // Confirmation dialog
  confirmationDialog: ConfirmationDialog;
  
  // Context menu
  contextMenu: {
    isOpen: boolean;
    x: number;
    y: number;
    items: any[];
  };
  
  // Fullscreen
  isFullscreen: boolean;
  fullscreenElement: string | null;
  
  // Actions
  openModal: (type: string, data?: any) => void;
  closeModal: (type?: string) => void;
  closeAllModals: () => void;
  
  addToast: (toast: Omit<Toast, 'id' | 'createdAt'>) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;
  
  openConfirmationDialog: (
    title: string,
    message: string,
    onConfirm?: () => void,
    onCancel?: () => void,
    confirmText?: string,
    cancelText?: string
  ) => void;
  closeConfirmationDialog: () => void;
  
  openContextMenu: (x: number, y: number, items: any[]) => void;
  closeContextMenu: () => void;
  
  setFullscreen: (isFullscreen: boolean, element?: string | null) => void;
  
  reset: () => void;
}

const initialState = {
  modals: [],
  toasts: [],
  confirmationDialog: {
    isOpen: false,
    title: '',
    message: '',
    onConfirm: undefined,
    onCancel: undefined,
  },
  contextMenu: {
    isOpen: false,
    x: 0,
    y: 0,
    items: [],
  },
  isFullscreen: false,
  fullscreenElement: null,
};

let toastId = 0;

export const useUiStore = create<UiState>()(
  devtools(
    (set, get) => ({
      ...initialState,
      
      openModal: (type, data) =>
        set((state) => ({
          modals: [...state.modals, { isOpen: true, type, data }],
        })),
      
      closeModal: (type) =>
        set((state) => ({
          modals: type 
            ? state.modals.filter((m) => m.type !== type)
            : state.modals.filter((m) => !m.isOpen),
        })),
      
      closeAllModals: () =>
        set({ modals: [] }),
      
      addToast: (toast) => {
        const id = String(++toastId);
        set((state) => ({
          toasts: [
            ...state.toasts,
            {
              id,
              createdAt: Date.now(),
              duration: toast.duration || 5000,
              ...toast,
            },
          ],
        }));
        return id;
      },
      
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
      
      clearToasts: () =>
        set({ toasts: [] }),
      
      openConfirmationDialog: (title, message, onConfirm, onCancel, confirmText, cancelText) =>
        set({
          confirmationDialog: {
            isOpen: true,
            title,
            message,
            onConfirm,
            onCancel,
            confirmText: confirmText || 'Confirm',
            cancelText: cancelText || 'Cancel',
          },
        }),
      
      closeConfirmationDialog: () =>
        set({
          confirmationDialog: {
            isOpen: false,
            title: '',
            message: '',
            onConfirm: undefined,
            onCancel: undefined,
          },
        }),
      
      openContextMenu: (x, y, items) =>
        set({
          contextMenu: {
            isOpen: true,
            x,
            y,
            items,
          },
        }),
      
      closeContextMenu: () =>
        set({
          contextMenu: {
            isOpen: false,
            x: 0,
            y: 0,
            items: [],
          },
        }),
      
      setFullscreen: (isFullscreen, element) =>
        set({ isFullscreen, fullscreenElement: element }),
      
      reset: () => set(initialState),
    }),
    { name: 'UiStore' }
  )
);

// Selector hooks
export const useModals = () => useUiStore((state) => state.modals);
export const useToasts = () => useUiStore((state) => state.toasts);
export const useConfirmationDialog = () => useUiStore((state) => state.confirmationDialog);
export const useContextMenu = () => useUiStore((state) => state.contextMenu);
export const useIsFullscreen = () => useUiStore((state) => state.isFullscreen);
export const useFullscreenElement = () => useUiStore((state) => state.fullscreenElement);

// Helper hooks
export const useIsModalOpen = (type: string) => 
  useUiStore((state) => 
    state.modals.some((m) => m.type === type && m.isOpen)
  );

export const useModalData = <T>(type: string) => 
  useUiStore((state) => 
    state.modals.find((m) => m.type === type && m.isOpen)?.data as T | undefined
  );

export const useIsContextMenuOpen = () => 
  useUiStore((state) => state.contextMenu.isOpen);

export const useContextMenuPosition = () => 
  useUiStore((state) => ({
    x: state.contextMenu.x,
    y: state.contextMenu.y,
  }));

export const useContextMenuItems = () => 
  useUiStore((state) => state.contextMenu.items);
