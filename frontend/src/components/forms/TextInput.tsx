export interface TextInputProps {
  label?: string;
  value?: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  mono?: boolean;
  type?: string;
  name?: string;
}

export function TextInput({ label, value, onChange, placeholder, mono, type = "text", name }: TextInputProps) {
  return (
    <label className="qf-input">
      {label && <span>{label}</span>}
      <input
        type={type}
        name={name}
        value={value || ''}
        onChange={(e) => onChange && onChange(e.target.value)}
        placeholder={placeholder}
        style={mono ? { fontFamily: 'var(--font-mono)', fontSize: 12.5 } : undefined}
      />
    </label>
  );
}
