import { Slot } from '@radix-ui/react-slot'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

// shadcn-style local component with native semantics and Radix composition.
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean
  variant?: 'primary' | 'secondary' | 'ghost'
}
export function Button({ asChild = false, variant = 'primary', className, ...props }: ButtonProps) {
  const Component = asChild ? Slot : 'button'
  return <Component className={cn('button', 'button-' + variant, className)} {...props} />
}
