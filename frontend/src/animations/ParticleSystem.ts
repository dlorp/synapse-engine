/**
 * Particle System with Physics
 *
 * High-performance particle engine with realistic physics simulation.
 * Foundation for fire, plasma, smoke, and other particle effects.
 *
 * Features:
 * - Full physics simulation (velocity, acceleration, forces)
 * - Multiple emitter types (point, line, area, burst)
 * - Force fields (gravity, wind, attraction, repulsion)
 * - Particle lifecycle management
 * - Optimized for 1000+ particles at 60fps
 * - Phosphor glow effect
 */

interface Vector2D {
  x: number;
  y: number;
}

interface Particle {
  // Position
  x: number;
  y: number;

  // Velocity
  vx: number;
  vy: number;

  // Acceleration
  ax: number;
  ay: number;

  // Visual properties
  size: number;
  color: string;
  alpha: number;
  rotation: number;
  rotationSpeed: number;

  // Lifecycle
  age: number;
  maxAge: number;
  alive: boolean;

  // Physics properties
  mass: number;
  friction: number;
}

interface EmitterConfig {
  type?: 'point' | 'line' | 'area' | 'burst'; // Emitter type
  x?: number; // X position
  y?: number; // Y position
  width?: number; // Width (for line/area emitters)
  height?: number; // Height (for area emitters)
  angle?: number; // Emission angle in degrees (0 = right)
  spread?: number; // Angle spread in degrees
  rate?: number; // Particles per second
  particlesPerEmit?: number; // Particles per emission
  burstSize?: number; // Particles in burst (for burst type)
}

interface ParticleConfig {
  minSize?: number;
  maxSize?: number;
  minSpeed?: number;
  maxSpeed?: number;
  minLife?: number; // milliseconds
  maxLife?: number; // milliseconds
  color?: string | string[]; // Single color or gradient
  startAlpha?: number;
  endAlpha?: number;
  gravity?: Vector2D;
  friction?: number;
  rotation?: boolean;
  rotationSpeed?: number;
  glowIntensity?: number;
}

interface ParticleSystemConfig {
  maxParticles?: number;
  backgroundColor?: string;
  emitter?: EmitterConfig;
  particle?: ParticleConfig;
}

export class ParticleSystem {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private particles: Particle[] = [];
  private config: Required<ParticleSystemConfig>;
  private emitterConfig: Required<EmitterConfig>;
  private particleConfig: Required<ParticleConfig>;
  private animationId: number | null = null;
  private lastEmitTime: number = 0;
  private lastUpdateTime: number = 0;
  private forces: Array<{ type: 'gravity' | 'wind' | 'attract' | 'repel'; force: Vector2D; x?: number; y?: number; radius?: number }> = [];

  constructor(canvas: HTMLCanvasElement, config: ParticleSystemConfig = {}) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D context not available');
    this.ctx = ctx;

    // Default emitter config
    this.emitterConfig = {
      type: config.emitter?.type || 'point',
      x: config.emitter?.x !== undefined ? config.emitter.x : canvas.width / 2,
      y: config.emitter?.y !== undefined ? config.emitter.y : canvas.height / 2,
      width: config.emitter?.width || 0,
      height: config.emitter?.height || 0,
      angle: config.emitter?.angle || -90, // Up by default
      spread: config.emitter?.spread || 30,
      rate: config.emitter?.rate || 30,
      particlesPerEmit: config.emitter?.particlesPerEmit || 1,
      burstSize: config.emitter?.burstSize || 50,
    };

    // Default particle config
    this.particleConfig = {
      minSize: config.particle?.minSize || 2,
      maxSize: config.particle?.maxSize || 5,
      minSpeed: config.particle?.minSpeed || 50,
      maxSpeed: config.particle?.maxSpeed || 150,
      minLife: config.particle?.minLife || 1000,
      maxLife: config.particle?.maxLife || 3000,
      color: config.particle?.color || '#ff9500',
      startAlpha: config.particle?.startAlpha || 1,
      endAlpha: config.particle?.endAlpha || 0,
      gravity: config.particle?.gravity || { x: 0, y: 0 },
      friction: config.particle?.friction || 0.98,
      rotation: config.particle?.rotation || false,
      rotationSpeed: config.particle?.rotationSpeed || 0.1,
      glowIntensity: config.particle?.glowIntensity || 5,
    };

    // Default system config
    this.config = {
      maxParticles: config.maxParticles || 1000,
      backgroundColor: config.backgroundColor || 'transparent',
      emitter: this.emitterConfig,
      particle: this.particleConfig,
    };
  }

  /**
   * Create a single particle
   */
  private createParticle(x: number, y: number, angle?: number): Particle {
    const { minSize, maxSize, minSpeed, maxSpeed, minLife, maxLife, color, startAlpha, friction, rotation, rotationSpeed } = this.particleConfig;

    // Random size
    const size = minSize + Math.random() * (maxSize - minSize);

    // Random speed and direction
    const speed = minSpeed + Math.random() * (maxSpeed - minSpeed);
    const baseAngle = angle !== undefined ? angle : this.emitterConfig.angle;
    const spread = this.emitterConfig.spread;
    const particleAngle = (baseAngle + (Math.random() - 0.5) * spread) * (Math.PI / 180);

    const vx = Math.cos(particleAngle) * speed;
    const vy = Math.sin(particleAngle) * speed;

    // Random lifetime
    const maxAge = minLife + Math.random() * (maxLife - minLife);

    // Color selection
    const particleColor = Array.isArray(color)
      ? color[Math.floor(Math.random() * color.length)] ?? '#ff9500'
      : color;

    return {
      x,
      y,
      vx,
      vy,
      ax: 0,
      ay: 0,
      size,
      color: particleColor,
      alpha: startAlpha,
      rotation: 0,
      rotationSpeed: rotation ? (Math.random() - 0.5) * rotationSpeed : 0,
      age: 0,
      maxAge,
      alive: true,
      mass: size,
      friction,
    };
  }

  /**
   * Emit particles based on emitter type
   */
  private emitParticles(count: number): void {
    const { type, x, y, width, height } = this.emitterConfig;

    for (let i = 0; i < count; i++) {
      let particleX = x;
      let particleY = y;
      let angle: number | undefined;

      switch (type) {
        case 'point':
          // Already set to x, y
          break;

        case 'line':
          // Random position along line
          particleX = x + Math.random() * width;
          particleY = y;
          break;

        case 'area':
          // Random position within area
          particleX = x + Math.random() * width;
          particleY = y + Math.random() * height;
          break;

        case 'burst':
          // Emit in all directions
          angle = Math.random() * 360;
          break;
      }

      if (this.particles.length < this.config.maxParticles) {
        this.particles.push(this.createParticle(particleX, particleY, angle));
      }
    }
  }

  /**
   * Add a force field
   */
  public addForce(
    type: 'gravity' | 'wind' | 'attract' | 'repel',
    force: Vector2D,
    x?: number,
    y?: number,
    radius?: number
  ): void {
    this.forces.push({ type, force, x, y, radius });
  }

  /**
   * Clear all force fields
   */
  public clearForces(): void {
    this.forces = [];
  }

  /**
   * Apply forces to a particle
   */
  private applyForces(particle: Particle): void {
    // Reset acceleration
    particle.ax = this.particleConfig.gravity.x;
    particle.ay = this.particleConfig.gravity.y;

    // Apply each force
    this.forces.forEach((field) => {
      switch (field.type) {
        case 'gravity':
        case 'wind':
          particle.ax += field.force.x;
          particle.ay += field.force.y;
          break;

        case 'attract':
        case 'repel':
          if (field.x !== undefined && field.y !== undefined) {
            const dx = field.x - particle.x;
            const dy = field.y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (field.radius === undefined || distance < field.radius) {
              const strength = field.type === 'attract' ? 1 : -1;
              const force = (strength * field.force.x) / (distance * distance + 1);
              particle.ax += (dx / distance) * force;
              particle.ay += (dy / distance) * force;
            }
          }
          break;
      }
    });
  }

  /**
   * Update particle physics and lifecycle
   */
  private updateParticle(particle: Particle, deltaTime: number): void {
    const dt = deltaTime / 1000; // Convert to seconds

    // Apply forces
    this.applyForces(particle);

    // Update velocity
    particle.vx += particle.ax * dt;
    particle.vy += particle.ay * dt;

    // Apply friction
    particle.vx *= particle.friction;
    particle.vy *= particle.friction;

    // Update position
    particle.x += particle.vx * dt;
    particle.y += particle.vy * dt;

    // Update rotation
    particle.rotation += particle.rotationSpeed;

    // Update age and alpha
    particle.age += deltaTime;
    const lifeProgress = particle.age / particle.maxAge;
    particle.alpha = this.particleConfig.startAlpha +
      (this.particleConfig.endAlpha - this.particleConfig.startAlpha) * lifeProgress;

    // Check if particle should die
    if (particle.age >= particle.maxAge ||
        particle.x < -50 || particle.x > this.canvas.width + 50 ||
        particle.y < -50 || particle.y > this.canvas.height + 50) {
      particle.alive = false;
    }
  }

  /**
   * Draw a single particle
   */
  private drawParticle(particle: Particle): void {
    const { glowIntensity } = this.particleConfig;

    this.ctx.save();

    // Set glow
    this.ctx.shadowColor = particle.color;
    this.ctx.shadowBlur = glowIntensity * particle.alpha;

    // Set alpha
    this.ctx.globalAlpha = particle.alpha;

    // Translate and rotate
    this.ctx.translate(particle.x, particle.y);
    if (particle.rotation !== 0) {
      this.ctx.rotate(particle.rotation);
    }

    // Draw particle as circle
    this.ctx.fillStyle = particle.color;
    this.ctx.beginPath();
    this.ctx.arc(0, 0, particle.size, 0, Math.PI * 2);
    this.ctx.fill();

    this.ctx.restore();
  }

  /**
   * Emit particles based on rate
   */
  private handleEmission(currentTime: number): void {
    if (this.emitterConfig.type === 'burst') {
      // Burst emits once
      return;
    }

    const timeSinceLastEmit = currentTime - this.lastEmitTime;
    const emitInterval = 1000 / this.emitterConfig.rate;

    if (timeSinceLastEmit >= emitInterval) {
      this.emitParticles(this.emitterConfig.particlesPerEmit);
      this.lastEmitTime = currentTime;
    }
  }

  /**
   * Trigger a burst emission
   */
  public burst(): void {
    this.emitParticles(this.emitterConfig.burstSize);
  }

  /**
   * Update emitter position
   */
  public setEmitterPosition(x: number, y: number): void {
    this.emitterConfig.x = x;
    this.emitterConfig.y = y;
  }

  /**
   * Render frame
   */
  private render(timestamp: number): void {
    const deltaTime = this.lastUpdateTime ? timestamp - this.lastUpdateTime : 16;
    this.lastUpdateTime = timestamp;

    // Clear canvas
    if (this.config.backgroundColor === 'transparent') {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    } else {
      this.ctx.fillStyle = this.config.backgroundColor;
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    // Handle emission
    this.handleEmission(timestamp);

    // Update particles
    this.particles.forEach((particle) => {
      if (particle.alive) {
        this.updateParticle(particle, deltaTime);
      }
    });

    // Remove dead particles
    this.particles = this.particles.filter((p) => p.alive);

    // Draw particles
    this.particles.forEach((particle) => {
      this.drawParticle(particle);
    });

    // Continue animation
    this.animationId = requestAnimationFrame((ts) => this.render(ts));
  }

  /**
   * Start particle system
   */
  public start(): void {
    if (this.animationId !== null) {
      this.stop();
    }
    this.lastUpdateTime = 0;
    this.lastEmitTime = 0;
    this.animationId = requestAnimationFrame((ts) => this.render(ts));
  }

  /**
   * Stop particle system
   */
  public stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /**
   * Clear all particles
   */
  public clear(): void {
    this.particles = [];
  }

  /**
   * Update configuration
   */
  public updateConfig(config: Partial<ParticleSystemConfig>): void {
    if (config.emitter) {
      this.emitterConfig = { ...this.emitterConfig, ...config.emitter };
    }
    if (config.particle) {
      this.particleConfig = { ...this.particleConfig, ...config.particle };
    }
    if (config.maxParticles !== undefined) {
      this.config.maxParticles = config.maxParticles;
    }
    if (config.backgroundColor !== undefined) {
      this.config.backgroundColor = config.backgroundColor;
    }
  }

  /**
   * Resize canvas
   */
  public resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
  }

  /**
   * Get particle count
   */
  public getParticleCount(): number {
    return this.particles.length;
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.stop();
    this.clear();
    this.clearForces();
  }
}
