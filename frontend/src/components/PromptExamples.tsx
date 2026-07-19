const examples = [
  "Draw a circle of radius 50 mm at center 100,100.",
  "Draw a half circle of diameter 120 mm facing upward.",
  "Draw a straight line of 300 mm at 45 degrees.",
  "Draw an ellipse with major axis 200 mm and minor axis 100 mm.",
  "Draw an arc radius 80 start angle 0 end angle 120 at center 100,100.",
  "Draw a parabola with width 300 mm and height 150 mm.",
  "Draw a slot of total length 300 mm and width 80 mm.",
  "Increase circle radius to 75 mm.",
  "Move the shape 20 mm upward.",
  "Add dimensions."
];

export default function PromptExamples({ onUse }: { onUse: (text: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {examples.map((example) => (
        <button key={example} className="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition hover:border-blue-400 hover:text-blue-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-blue-500 dark:hover:text-blue-300" onClick={() => onUse(example)}>
          {example}
        </button>
      ))}
    </div>
  );
}
