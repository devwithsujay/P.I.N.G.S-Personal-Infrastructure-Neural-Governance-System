import React from 'react'
import { Modal, Button } from '@heroui/react'

export default function ConfirmDialog({ open, title, message, confirmLabel = 'Confirm', cancelLabel = 'Cancel', danger = false, onConfirm, onCancel }) {
  return (
    <Modal.Backdrop isOpen={open} onOpenChange={(isOpen) => { if (!isOpen) onCancel() }}>
      <Modal.Container size="sm">
        <Modal.Dialog className="sm:max-w-sm">
          <Modal.Header>
            <Modal.Heading className="text-sm font-semibold">{title}</Modal.Heading>
          </Modal.Header>
          <Modal.Body>
            <p className="text-xs text-text-secondary leading-relaxed">{message}</p>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="tertiary" size="sm" slot="close">{cancelLabel}</Button>
            <Button
              size="sm"
              variant={danger ? 'danger' : 'primary'}
              onPress={onConfirm}
            >
              {confirmLabel}
            </Button>
          </Modal.Footer>
        </Modal.Dialog>
      </Modal.Container>
    </Modal.Backdrop>
  )
}
