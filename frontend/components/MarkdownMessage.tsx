"use client";

function inlineFormat(text: string): string {
  return text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

export default function MarkdownMessage({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    const trimmed = line.trim();
    if (!trimmed) {
      elements.push(<br key={`br-${i}`} />);
      return;
    }
    if (trimmed.startsWith("- ")) {
      elements.push(
        <li key={i} className="text-sm text-[var(--text-primary)]" dangerouslySetInnerHTML={{ __html: inlineFormat(trimmed.slice(2)) }} />
      );
      return;
    }
    elements.push(
      <p key={i} className="text-sm text-[var(--text-primary)]" dangerouslySetInnerHTML={{ __html: inlineFormat(trimmed) }} />
    );
  });

  const hasList = lines.some((l) => l.trim().startsWith("- "));
  if (hasList) {
    const result: React.ReactNode[] = [];
    let listItems: React.ReactNode[] = [];
    elements.forEach((el, idx) => {
      if (typeof el === "object" && el !== null && "type" in el && el.type === "li") {
        listItems.push(el);
      } else {
        if (listItems.length) {
          result.push(<ul key={`ul-${idx}`} className="list-disc pl-4 my-1">{listItems}</ul>);
          listItems = [];
        }
        result.push(el);
      }
    });
    if (listItems.length) result.push(<ul key="ul-final" className="list-disc pl-4 my-1">{listItems}</ul>);
    return <div className="prose-socialiq space-y-0.5">{result}</div>;
  }

  return <div className="prose-socialiq space-y-0.5">{elements}</div>;
}
