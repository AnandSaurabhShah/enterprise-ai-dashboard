import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const Button = React.forwardRef<HTMLButtonElement, any>(
  ({ className, variant = 'primary', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-800 disabled:opacity-50 disabled:pointer-events-none",
          {
            'bg-[#115E59] text-white hover:bg-[#0f4d49]': variant === 'primary',
            'bg-slate-100 text-slate-900 hover:bg-slate-200': variant === 'secondary',
            'border border-slate-200 hover:bg-slate-100': variant === 'outline',
            'hover:bg-slate-100': variant === 'ghost',
            'h-9 px-3': size === 'sm',
            'h-10 py-2 px-4': size === 'md',
            'h-11 px-8': size === 'lg',
            'w-full': props.className?.includes('w-full'),
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export const Input = React.forwardRef<HTMLInputElement, any>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#115E59] focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export const Textarea = React.forwardRef<HTMLTextAreaElement, any>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#115E59] focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export const Select = React.forwardRef<HTMLSelectElement, any>(
  ({ className, options, placeholder, ...props }, ref) => {
    return (
      <select
        className={cn(
          "flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#115E59] focus:border-transparent disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      >
        {placeholder && <option value="" disabled hidden>{placeholder}</option>}
        {options.map((opt: string) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    );
  }
);
Select.displayName = "Select";

export function Card({ className, children, ...props }: any) {
  return (
    <div className={cn("rounded-xl border border-slate-200 bg-white text-slate-950 shadow-sm", className)} {...props}>
      {children}
    </div>
  );
}

export function Badge({ className, variant = 'default', children, ...props }: any) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          'bg-[#DCFCE7] text-[#166534] border-transparent': variant === 'live',
          'bg-[#FFEDD5] text-[#9A3412] border-transparent': variant === 'preview',
          'bg-slate-100 text-slate-800 border-transparent': variant === 'default',
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function Terminal({ children, className }: { children?: React.ReactNode, className?: string }) {
  return (
    <div className={cn("rounded-md bg-[#0F172A] p-4 text-sm font-mono text-slate-300 shadow-inner overflow-x-auto", className)}>
      {children || "Results will appear here."}
    </div>
  );
}
