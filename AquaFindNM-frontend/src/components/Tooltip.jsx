import { useState } from 'react'
import { HelpCircle } from 'lucide-react'

export default function Tooltip({ text }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative inline-flex items-center ml-1.5">

      {/* Help icon */}
      <button
        type="button"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        onClick={() => setVisible(!visible)}
        className="flex items-center justify-center rounded-full transition-colors"
        style={{ color: 'var(--text-light)' }}
        onMouseOver={e => e.currentTarget.style.color = 'var(--green-1)'}
        onMouseOut={e => e.currentTarget.style.color = 'var(--text-light)'}
      >
        <HelpCircle size={15} />
      </button>

      {/* Tooltip bubble */}
      {visible && (
        <div
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 rounded-xl px-3 py-2.5 text-xs shadow-lg"
          style={{
            backgroundColor: 'var(--green-2)',
            color: 'var(--green-4)',
            lineHeight: '1.5',
          }}
        >
          {text}

          {/* little triangle pointer */}
          <div
            className="absolute top-full left-1/2 -translate-x-1/2"
            style={{
              width: 0,
              height: 0,
              borderLeft: '6px solid transparent',
              borderRight: '6px solid transparent',
              borderTop: '6px solid var(--green-2)',
            }}
          />
        </div>
      )}
    </div>
  )
}