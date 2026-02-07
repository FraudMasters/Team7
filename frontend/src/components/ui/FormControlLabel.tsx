import React from 'react';
import styled from '@emotion/styled';
import { useEmotionTheme, EmotionTheme } from '../../contexts/EmotionThemeContext';
import { Checkbox } from './Checkbox';
import { Switch } from './Switch';
import { Radio } from './Radio';

export interface FormControlLabelProps {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  sx?: React.CSSProperties | ((theme: EmotionTheme) => React.CSSProperties);
  checked?: boolean;
  defaultChecked?: boolean;
  disabled?: boolean;
  label: React.ReactNode;
  labelPlacement?: 'end' | 'start' | 'top' | 'bottom';
  onChange?: (event: React.ChangeEvent<HTMLInputElement>, checked: boolean) => void;
  value?: string;
  control?: React.ReactNode;
  name?: string;
  required?: boolean;
}

const LabelContainer = styled.label<{ disabled?: boolean }>`
  display: inline-flex;
  align-items: center;
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  vertical-align: middle;
  user-select: none;
`;

const LabelText = styled.span<{ disabled?: boolean }>`
  margin-left: 8px;
  font-size: 0.875rem;
  color: ${({ disabled }) => (disabled ? 'rgba(0, 0, 0, 0.6)' : 'rgba(0, 0, 0, 0.87)')};
`;

export const FormControlLabel: React.FC<FormControlLabelProps> = ({
  checked,
  defaultChecked,
  disabled = false,
  label,
  labelPlacement = 'end',
  onChange,
  value,
  control,
  name,
  required,
  className,
  style,
  sx,
}) => {
  const { theme } = useEmotionTheme();

  const sxStyles = typeof sx === 'function' ? sx(theme) : sx;

  // Default to checkbox if no control provided
  const defaultControl = control || (
    <Checkbox
      checked={checked}
      defaultChecked={defaultChecked}
      onChange={onChange}
      value={value}
      name={name}
      disabled={disabled}
    />
  );

  const renderLabel = () => (
    <LabelText disabled={disabled}>
      {label}
      {required && <span style={{ color: 'inherit', marginLeft: '2px' }}>*</span>}
    </LabelText>
  );

  let content: React.ReactNode;

  switch (labelPlacement) {
    case 'start':
      content = (
        <>
          {renderLabel()}
          {defaultControl}
        </>
      );
      break;
    case 'top':
      content = (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {renderLabel()}
          {defaultControl}
        </div>
      );
      break;
    case 'bottom':
      content = (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          {defaultControl}
          {renderLabel()}
        </div>
      );
      break;
    case 'end':
    default:
      content = (
        <>
          {defaultControl}
          {renderLabel()}
        </>
      );
      break;
  }

  return (
    <LabelContainer
      className={className}
      style={{ ...style, ...sxStyles }}
      disabled={disabled}
    >
      {content}
    </LabelContainer>
  );
};

FormControlLabel.displayName = 'FormControlLabel';

export default FormControlLabel;
