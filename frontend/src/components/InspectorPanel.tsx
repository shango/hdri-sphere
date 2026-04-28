import { useEditorStore } from '@/stores/editorStore';
import { useProjectState } from '@/hooks/useProjectState';
import { Section } from '@/components/ui/Section';
import { Stat } from '@/components/ui/Stat';
import { Pill } from '@/components/ui/Pill';
import { ExposureSlider } from '@/components/ExposureSlider';
import { TechniquePanel } from '@/components/TechniquePanel';
import { ExportButton } from '@/components/ExportButton';
import { EquirectStrip } from '@/components/EquirectStrip';

export function InspectorPanel(): JSX.Element {
  const sourceFilename = useEditorStore((s) => s.sourceFilename);
  const imageWidth = useEditorStore((s) => s.imageWidth);
  const imageHeight = useEditorStore((s) => s.imageHeight);
  const ballCenter = useEditorStore((s) => s.ballCenter);
  const ballRadius = useEditorStore((s) => s.ballRadius);
  const technique = useEditorStore((s) => s.technique);
  const state = useProjectState();
  const cached = state.data?.cached_techniques ?? [];
  const hasMask = state.data?.has_mask ?? false;

  const aspectMP = ((imageWidth * imageHeight) / 1_000_000).toFixed(1);

  return (
    <aside className="flex w-[22rem] shrink-0 flex-col overflow-y-auto border-l border-ink-700 bg-ink-900/60">
      <Section title="Plate">
        <div className="space-y-1">
          <Stat label="File" value={<span className="font-mono text-xs">{sourceFilename}</span>} mono={false} />
          <Stat
            label="Resolution"
            value={`${imageWidth} × ${imageHeight}`}
          />
          <Stat label="Pixels" value={`${aspectMP} MP`} />
        </div>
      </Section>

      <Section
        title="Ball"
        aside={
          <Pill tone="lime">
            <span>Auto-detected</span>
          </Pill>
        }
      >
        <div className="space-y-1">
          <Stat label="Center" value={`${ballCenter[0]}, ${ballCenter[1]}`} />
          <Stat label="Radius" value={`${ballRadius} px`} />
        </div>
      </Section>

      <Section
        title="Mask"
        aside={
          hasMask ? (
            <Pill tone="lime">Active</Pill>
          ) : (
            <Pill tone="amber">Not set</Pill>
          )
        }
      >
        <p className="text-xs leading-relaxed text-ink-300">
          Switch to the <span className="text-lime-400">Mask</span> view to
          paint over what should be replaced. The mask is auto-generated on
          upload — refine it where the photographer / tripod isn't covered.
        </p>
      </Section>

      <Section title="Exposure" dense>
        <ExposureSlider />
      </Section>

      <Section
        title="Technique"
        aside={
          cached.length ? (
            <Pill tone="muted">
              {cached.length} cached: {cached.join(', ')}
            </Pill>
          ) : null
        }
      >
        <TechniquePanel />
        <p className="mt-3 text-2xs leading-relaxed text-ink-500">
          Currently rendering with{' '}
          <span className="font-mono text-ink-300">{technique}</span>. Switching
          tiers re-runs the inpaint; cached results return instantly.
        </p>
      </Section>

      <Section title="Equirect preview" dense>
        <EquirectStrip />
      </Section>

      <Section title="Export">
        <ExportButton />
      </Section>
    </aside>
  );
}
