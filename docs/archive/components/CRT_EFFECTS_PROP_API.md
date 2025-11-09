# CRT Effects Component API Reference

Complete prop documentation for the enhanced CRTMonitor and AnimatedScanlines components.

---

## CRTMonitor Component

**Import:**
```tsx
import { CRTMonitor } from '@/components/terminal';
```

### Props

```typescript
interface CRTMonitorProps {
  children: ReactNode;
  intensity?: CRTIntensity;           // 'subtle' | 'medium' | 'intense'
  bloomIntensity?: number;            // 0-1 (default: 0.3)
  enableScanlines?: boolean;          // default: true
  scanlinesEnabled?: boolean;         // alias for enableScanlines (deprecated)
  enableCurvature?: boolean;          // default: true
  curvatureEnabled?: boolean;         // alias for enableCurvature (deprecated)
  enableAberration?: boolean;         // default: true
  enableVignette?: boolean;           // default: true
  scanlineSpeed?: ScanlineSpeed;      // 'slow' | 'medium' | 'fast'
  className?: string;
  ariaLabel?: string;
}
```

### Prop Details

#### `intensity`
- **Type:** `'subtle' | 'medium' | 'intense'`
- **Default:** `'medium'`
- **Description:** Overall CRT effect intensity (phosphor glow, vignette strength)

**Examples:**
```tsx
<CRTMonitor intensity="subtle">   {/* Light effects */}
<CRTMonitor intensity="medium">   {/* Balanced (default) */}
<CRTMonitor intensity="intense">  {/* Maximum CRT aesthetic */}
```

---

#### `bloomIntensity` ⭐ NEW
- **Type:** `number` (0-1)
- **Default:** `0.3`
- **Description:** Phosphor bloom glow intensity

**Values:**
- `0` - No bloom (performance mode, bloom layer not rendered)
- `0.3` - Subtle glow (default, recommended for readability)
- `0.6` - Moderate bloom (hero sections, banners)
- `1.0` - Maximum phosphor bleeding effect

**Examples:**
```tsx
<CRTMonitor bloomIntensity={0}>     {/* No bloom */}
<CRTMonitor bloomIntensity={0.3}>   {/* Default */}
<CRTMonitor bloomIntensity={0.6}>   {/* Strong glow */}
<CRTMonitor bloomIntensity={1.0}>   {/* Maximum bloom */}
```

**Technical Details:**
- Blur amount: `blur(${bloomIntensity * 20}px)` (0-20px)
- Uses `mix-blend-mode: screen` for glow effect
- GPU accelerated with will-change hints
- Conditionally rendered (no DOM node if intensity=0)

---

#### `enableScanlines` / `scanlinesEnabled`
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable/disable animated scanline overlay

**Examples:**
```tsx
<CRTMonitor scanlinesEnabled={true}>   {/* Scanlines on */}
<CRTMonitor scanlinesEnabled={false}>  {/* No scanlines */}
```

**Note:** Both prop names work (backward compatibility). Use `scanlinesEnabled` for consistency with new API.

---

#### `enableCurvature` / `curvatureEnabled` ⭐ ENHANCED
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable/disable screen curvature (15° perspective)

**Examples:**
```tsx
<CRTMonitor curvatureEnabled={true}>   {/* Curved screen */}
<CRTMonitor curvatureEnabled={false}>  {/* Flat screen */}
```

**Technical Details:**
- Outer container: `perspective(1000px)`
- Inner screen: `translateZ(-5px)` for depth
- Combined with vignette for edge darkening
- Subtle effect, doesn't interfere with readability

---

#### `enableAberration`
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable/disable chromatic aberration (RGB split)

**Examples:**
```tsx
<CRTMonitor enableAberration={true}>   {/* RGB split effect */}
<CRTMonitor enableAberration={false}>  {/* Clean text */}
```

---

#### `enableVignette`
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable/disable vignette overlay (darkened corners)

**Examples:**
```tsx
<CRTMonitor enableVignette={true}>   {/* Dark edges */}
<CRTMonitor enableVignette={false}>  {/* No vignette */}
```

---

#### `scanlineSpeed`
- **Type:** `'slow' | 'medium' | 'fast'`
- **Default:** `'medium'`
- **Description:** Scanline animation speed

**Values:**
- `'slow'` - 8 seconds per cycle
- `'medium'` - 4 seconds per cycle (default)
- `'fast'` - 2 seconds per cycle

**Examples:**
```tsx
<CRTMonitor scanlineSpeed="slow">     {/* Slow drift */}
<CRTMonitor scanlineSpeed="medium">   {/* Default */}
<CRTMonitor scanlineSpeed="fast">     {/* Quick motion */}
```

---

#### `className`
- **Type:** `string`
- **Default:** `''`
- **Description:** Additional CSS class name

**Example:**
```tsx
<CRTMonitor className="custom-panel">
  <div>Content</div>
</CRTMonitor>
```

---

#### `ariaLabel`
- **Type:** `string`
- **Default:** `'CRT Monitor Display'`
- **Description:** ARIA label for accessibility

**Example:**
```tsx
<CRTMonitor ariaLabel="Neural Status Panel">
  <div>Status data</div>
</CRTMonitor>
```

---

## AnimatedScanlines Component

**Import:**
```tsx
import { AnimatedScanlines } from '@/components/terminal';
```

### Props

```typescript
interface AnimatedScanlinesProps {
  speed?: ScanlineSpeed;      // 'slow' | 'medium' | 'fast'
  opacity?: number;            // 0-1 (default: 0.2)
  intensity?: number;          // alias for opacity (deprecated)
  enabled?: boolean;           // default: true
}
```

### Prop Details

#### `speed`
- **Type:** `'slow' | 'medium' | 'fast'`
- **Default:** `'medium'`
- **Description:** Animation speed

**Examples:**
```tsx
<AnimatedScanlines speed="slow" />
<AnimatedScanlines speed="medium" />
<AnimatedScanlines speed="fast" />
```

---

#### `opacity` / `intensity`
- **Type:** `number` (0-1)
- **Default:** `0.2`
- **Description:** Scanline visibility

**Examples:**
```tsx
<AnimatedScanlines opacity={0.1} />   {/* Subtle */}
<AnimatedScanlines opacity={0.2} />   {/* Default */}
<AnimatedScanlines opacity={0.3} />   {/* Strong */}
```

**Note:** Both prop names work. `opacity` is preferred.

---

#### `enabled`
- **Type:** `boolean`
- **Default:** `true`
- **Description:** Enable/disable scanlines

**Examples:**
```tsx
<AnimatedScanlines enabled={true} />
<AnimatedScanlines enabled={false} />
```

---

## Common Use Cases

### 1. Default CRT Aesthetic
```tsx
<CRTMonitor>
  <YourContent />
</CRTMonitor>
```

### 2. Hero Section (Strong Bloom)
```tsx
<CRTMonitor
  bloomIntensity={0.6}
  intensity="intense"
  scanlineSpeed="slow"
>
  <HeroBanner />
</CRTMonitor>
```

### 3. Performance Mode (Mobile)
```tsx
<CRTMonitor
  bloomIntensity={0}
  scanlinesEnabled={false}
  curvatureEnabled={false}
  intensity="subtle"
>
  <MobileContent />
</CRTMonitor>
```

### 4. Clean Text Panel
```tsx
<CRTMonitor
  bloomIntensity={0.2}
  enableAberration={false}
>
  <TextContent />
</CRTMonitor>
```

### 5. Maximum CRT Effect
```tsx
<CRTMonitor
  bloomIntensity={1.0}
  intensity="intense"
  curvatureEnabled={true}
  scanlinesEnabled={true}
  scanlineSpeed="fast"
>
  <TerminalOutput />
</CRTMonitor>
```

---

## Performance Considerations

### High Performance Settings
```tsx
<CRTMonitor
  bloomIntensity={0}        // No bloom layer
  scanlinesEnabled={false}  // No scanline animation
  curvatureEnabled={false}  // No 3D transforms
  intensity="subtle"        // Minimal glow
/>
```

### Balanced Settings (Recommended)
```tsx
<CRTMonitor
  bloomIntensity={0.3}      // Subtle bloom
  scanlinesEnabled={true}   // Scanlines on
  curvatureEnabled={true}   // Curvature on
  intensity="medium"        // Medium glow
/>
```

### Visual Impact Settings
```tsx
<CRTMonitor
  bloomIntensity={0.6}      // Strong bloom
  scanlinesEnabled={true}   // Scanlines on
  curvatureEnabled={true}   // Curvature on
  intensity="intense"       // Maximum glow
/>
```

---

## Browser Support

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Bloom | ✅ | ✅ | ⚠️* | ✅ |
| Curvature | ✅ | ✅ | ✅ | ✅ |
| Scanlines | ✅ | ✅ | ✅ | ✅ |
| Vignette | ✅ | ✅ | ✅ | ✅ |
| Aberration | ✅ | ✅ | ✅ | ✅ |

*Safari may have reduced blur performance. Consider lowering bloom intensity to 0.2.

---

## Accessibility

All visual effects have proper accessibility support:

- **aria-hidden="true"** on all overlay layers
- **Reduced motion support** via CSS media query
- **Keyboard navigation** unaffected
- **Screen readers** ignore visual effects
- **Focus indicators** remain visible

**Reduced Motion:**
```css
@media (prefers-reduced-motion: reduce) {
  /* Animations disabled automatically */
  /* Bloom opacity reduced */
}
```

---

## TypeScript Types

```typescript
export type CRTIntensity = 'subtle' | 'medium' | 'intense';
export type ScanlineSpeed = 'slow' | 'medium' | 'fast';

export interface CRTMonitorProps {
  children: ReactNode;
  intensity?: CRTIntensity;
  bloomIntensity?: number;
  enableScanlines?: boolean;
  scanlinesEnabled?: boolean;
  enableCurvature?: boolean;
  curvatureEnabled?: boolean;
  enableAberration?: boolean;
  enableVignette?: boolean;
  scanlineSpeed?: ScanlineSpeed;
  className?: string;
  ariaLabel?: string;
}

export interface AnimatedScanlinesProps {
  speed?: ScanlineSpeed;
  opacity?: number;
  intensity?: number;
  enabled?: boolean;
}
```

---

## Testing Commands

```bash
# Build and start
docker-compose build --no-cache synapse_frontend
docker-compose up -d

# View logs
docker-compose logs -f synapse_frontend

# Access
open http://localhost:5173
```

---

**Full Documentation:** [CRT_EFFECTS_ENHANCEMENT_REPORT.md](./CRT_EFFECTS_ENHANCEMENT_REPORT.md)
