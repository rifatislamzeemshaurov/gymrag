'use client';

import { useRef, useState, useEffect } from 'react';
import { Send, Dumbbell, User, Info, Paperclip, PlusCircle } from 'lucide-react';

interface Product {
    category: string | null;
    brand_or_make: string | null;
    product_name: string | null;
    price: string | null;
    quantity_servings?: string | null;
    brand_overview?: string | null;
    review_and_efficacy?: string | null;
    specs: Record<string, string>;
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    products?: Product[];
    timestamp: Date;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

const SUGGESTIONS = [
    "I can't recover between sessions, what should I take?",
    'Recommend a pre-workout with high caffeine',
    "What's a good daily multivitamin?",
    'Upload a supplement label for alternatives',
];

const CATEGORY_META: Record<string, { label: string; classes: string }> = {
    whey_protein: { label: 'Whey Protein', classes: 'bg-teal-50 text-teal-700 ring-teal-600/20' },
    creatine: { label: 'Creatine', classes: 'bg-sky-50 text-sky-700 ring-sky-600/20' },
    pre_workout: { label: 'Pre-Workout', classes: 'bg-orange-50 text-orange-700 ring-orange-600/20' },
    post_workout: { label: 'Recovery', classes: 'bg-violet-50 text-violet-700 ring-violet-600/20' },
    multivitamin: { label: 'Multivitamin', classes: 'bg-amber-50 text-amber-700 ring-amber-600/20' },
};

const SPEC_LABELS: Record<string, string> = {
    protein_per_serving: 'Protein / Serving',
    protein_source: 'Source',
    creatine_per_serving: 'Creatine / Serving',
    creatine_form: 'Form',
    caffeine_per_serving: 'Caffeine / Serving',
    l_citrulline: 'L-Citrulline',
    beta_alanine: 'Beta-Alanine',
    amino_acids_per_serving: 'Aminos / Serving',
    glutamine_per_serving: 'Glutamine',
    electrolytes: 'Electrolytes',
    serving_size: 'Serving Size',
    key_nutrients: 'Key Nutrients',
    best_for: 'Best For',
};

const EXTRACTED_LABELS: Record<string, string> = {
    category: 'Category',
    brand_or_make: 'Brand',
    product_name: 'Product',
    price: 'Price',
    quantity_servings: 'Quantity / Servings',
    brand_overview: 'Overview',
    review_and_efficacy: 'Review',
    ...SPEC_LABELS,
};

// Fields that are prose, not short facts. Shown as text, not as pills.
const PROSE_FIELDS = new Set(['brand_overview', 'review_and_efficacy']);

// ---------------------------------------------------------------------------
// Display-only text polish.
//
// ragwire's metadata extractor lowercases every string it stores (not
// configurable; see backend/rag_engine.py's _titleize, which fixes brand and
// product names server-side). Spec values stay raw from the API, so this does
// the same job client-side: title-case short values, fix units and acronyms,
// and sentence-case prose. Purely cosmetic: the data driving search and
// filters is never touched.
// ---------------------------------------------------------------------------

const ACRONYMS: Record<string, string> = {
    bcaa: 'BCAA', eaa: 'EAA', hcl: 'HCl', hmb: 'HMB', zma: 'ZMA', epa: 'EPA',
    dha: 'DHA', iu: 'IU', usd: 'USD', coq10: 'CoQ10', d3: 'D3', b6: 'B6',
    b12: 'B12', k2: 'K2', dhea: 'DHEA',
};

const UNITS: Record<string, string> = { mg: 'mg', mcg: 'mcg', g: 'g', ml: 'ml', lbs: 'lbs', lb: 'lb' };

const BRAND_OVERRIDES: Record<string, string> = {
    ironforge: 'IronForge', northpeak: 'NorthPeak', purelift: 'PureLift',
    blackridge: 'BlackRidge', corestrong: 'CoreStrong',
};

function fixWord(word: string): string {
    const lower = word.toLowerCase();
    if (BRAND_OVERRIDES[lower]) return BRAND_OVERRIDES[lower];
    if (ACRONYMS[lower]) return ACRONYMS[lower];
    if (UNITS[lower]) return UNITS[lower];
    if (/^\d/.test(word)) return lower; // "300mg", "2.5g" stay as-is
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}

/** Title-cases short values, fixing known acronyms, units and brand names. */
function titleCase(text: string): string {
    return text.replace(/[A-Za-z0-9.]+/g, fixWord);
}

/** Sentence-cases prose instead of title-casing every word. */
function sentenceCase(text: string): string {
    const normalized = text.replace(/\s*\n+\s*/g, ' ').trim();
    const withAcronyms = normalized.replace(/[A-Za-z0-9]+/g, (run) => {
        const lower = run.toLowerCase();
        if (BRAND_OVERRIDES[lower]) return BRAND_OVERRIDES[lower];
        if (ACRONYMS[lower]) return ACRONYMS[lower];
        return run;
    });
    return withAcronyms.replace(/(^\s*[a-z])|([.!?]\s+)([a-z])/g, (_m, p1, p2, p3) =>
        p1 ? p1.toUpperCase() : `${p2}${p3.toUpperCase()}`
    );
}

/** A long spec value (e.g. a list of key nutrients) reads as a sentence, not
 * a label, so it renders as a line of text instead of a pill. */
function isLongValue(value: string): boolean {
    return value.length > 40 || value.includes('\n');
}

function ProductCard({ product }: { product: Product }) {
    const meta = product.category ? CATEGORY_META[product.category] : undefined;
    const specEntries = Object.entries(product.specs || {});
    const pillSpecs = specEntries.filter(([, value]) => !isLongValue(value));
    const longSpecs = specEntries.filter(([, value]) => isLongValue(value));
    const title = [product.brand_or_make, product.product_name].filter(Boolean).join(' - ');

    return (
        <div className="w-full rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold leading-snug text-slate-900">
                    {title || 'Unknown product'}
                </p>
                {meta && (
                    <span className={`flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ring-1 ring-inset ${meta.classes}`}>
                        {meta.label}
                    </span>
                )}
            </div>

            {product.brand_overview && (
                <p className="mt-1 text-xs text-slate-500">{sentenceCase(product.brand_overview)}</p>
            )}

            <div className="mt-2 flex flex-wrap gap-1.5">
                {product.quantity_servings && (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                        {titleCase(product.quantity_servings)}
                    </span>
                )}
                {product.price && (
                    <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
                        {product.price}
                    </span>
                )}
                {pillSpecs.map(([field, value]) => (
                    <span key={field} className="rounded-full bg-teal-50 px-2 py-0.5 text-[11px] font-medium text-teal-700 ring-1 ring-inset ring-teal-600/20">
                        {(SPEC_LABELS[field] || field) + ': ' + titleCase(value)}
                    </span>
                ))}
            </div>

            {longSpecs.map(([field, value]) => (
                <p key={field} className="mt-2 text-xs leading-relaxed text-slate-600">
                    <span className="font-medium text-slate-700">{SPEC_LABELS[field] || field}: </span>
                    {titleCase(value)}
                </p>
            ))}

            {product.review_and_efficacy && (
                <p className="mt-2 text-xs leading-relaxed text-slate-500">
                    {sentenceCase(product.review_and_efficacy)}
                </p>
            )}
        </div>
    );
}

function renderInline(text: string, keyPrefix: string) {
    // Splits on **bold** segments, the only inline markdown the assistant uses.
    const parts = text.split(/\*\*(.+?)\*\*/g);
    return parts.map((part, i) =>
        i % 2 === 1 ? <strong key={`${keyPrefix}-${i}`}>{part}</strong> : <span key={`${keyPrefix}-${i}`}>{part}</span>
    );
}

/** Minimal markdown-lite renderer: groups "- "/"* " bullet lines into a list,
 * renders **bold** inline, everything else as plain paragraphs. */
function FormattedText({ text }: { text: string }) {
    const lines = text.split('\n');
    const blocks: { type: 'p' | 'ul'; lines: string[] }[] = [];

    for (const rawLine of lines) {
        const line = rawLine.trim();
        const isBullet = line.startsWith('- ') || line.startsWith('* ');
        if (!line) continue;
        const content = isBullet ? line.slice(2) : line;
        const last = blocks[blocks.length - 1];
        const kind = isBullet ? 'ul' : 'p';
        if (last && last.type === kind && kind === 'ul') {
            last.lines.push(content);
        } else {
            blocks.push({ type: kind, lines: [content] });
        }
    }

    return (
        <div className="flex flex-col gap-1.5">
            {blocks.map((block, i) =>
                block.type === 'ul' ? (
                    <ul key={i} className="list-disc space-y-0.5 pl-4">
                        {block.lines.map((line, j) => (
                            <li key={j}>{renderInline(line, `${i}-${j}`)}</li>
                        ))}
                    </ul>
                ) : (
                    <p key={i}>{renderInline(block.lines[0], `${i}`)}</p>
                )
            )}
        </div>
    );
}

function BotAvatar({ size = 'sm' }: { size?: 'sm' | 'lg' }) {
    const box = size === 'lg' ? 'h-10 w-10' : 'h-7 w-7';
    const icon = size === 'lg' ? 'h-5 w-5' : 'h-3.5 w-3.5';
    return (
        <div className={`flex ${box} flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 text-white shadow-sm`}>
            <Dumbbell className={icon} />
        </div>
    );
}

function ThinkingIndicator({ stage }: { stage: string }) {
    return (
        <div className="animate-message-in flex items-end gap-2.5 justify-start">
            <BotAvatar />
            <div className="animate-shimmer rounded-2xl rounded-bl-md border border-slate-200 bg-gradient-to-r from-white via-teal-50 to-white bg-[length:200%_100%] px-4 py-2.5 shadow-sm">
                <p key={stage} className="animate-stage-fade flex items-center gap-2 text-xs font-medium text-slate-600">
                    <span className="flex gap-1">
                        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-500" />
                        <span className="delay-100 h-1.5 w-1.5 animate-bounce rounded-full bg-teal-500" />
                        <span className="delay-200 h-1.5 w-1.5 animate-bounce rounded-full bg-teal-500" />
                    </span>
                    {stage}
                </p>
            </div>
        </div>
    );
}

export default function GymRagAdvisor() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [thinkingStage, setThinkingStage] = useState<string>('Thinking through your question...');
    const [sessionId, setSessionId] = useState<string>('');
    const [streamingId, setStreamingId] = useState<string | null>(null);
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        const el = messagesContainerRef.current;
        if (!el) return;
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const appendMessage = (msg: Message) => setMessages(prev => [...prev, msg]);

    const startNewChat = () => {
        if (isLoading) return;
        setMessages([]);
        setSessionId('');
        setStreamingId(null);
        setInput('');
        inputRef.current?.focus();
    };

    const sendMessage = async (text?: string) => {
        const content = (text ?? input).trim();
        if (!content || isLoading) return;

        appendMessage({ id: crypto.randomUUID(), role: 'user', content, timestamp: new Date() });
        setInput('');
        setIsLoading(true);
        setThinkingStage('Thinking through your question...');

        try {
            const response = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
                body: JSON.stringify({ message: content, session_id: sessionId || undefined }),
            });

            if (!response.ok || !response.body) throw new Error('Failed to send message');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            const assistantId = crypto.randomUUID();
            let streamedContent = '';
            let assistantMessageStarted = false;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const chunks = buffer.split('\n\n');
                buffer = chunks.pop() ?? '';

                for (const chunk of chunks) {
                    const line = chunk.trim();
                    if (!line.startsWith('data:')) continue;
                    const evt = JSON.parse(line.slice(5).trim());

                    if (evt.type === 'status') {
                        setThinkingStage(evt.stage);
                    } else if (evt.type === 'token') {
                        streamedContent += evt.content;
                        if (!assistantMessageStarted) {
                            assistantMessageStarted = true;
                            setStreamingId(assistantId);
                            appendMessage({
                                id: assistantId,
                                role: 'assistant',
                                content: streamedContent,
                                timestamp: new Date(),
                            });
                        } else {
                            const snapshot = streamedContent;
                            setMessages(prev =>
                                prev.map(m => (m.id === assistantId ? { ...m, content: snapshot } : m))
                            );
                        }
                    } else if (evt.type === 'final') {
                        if (!sessionId && evt.session_id) setSessionId(evt.session_id);
                        setStreamingId(null);
                        if (assistantMessageStarted) {
                            setMessages(prev =>
                                prev.map(m =>
                                    m.id === assistantId ? { ...m, content: evt.response, products: evt.products } : m
                                )
                            );
                        } else {
                            appendMessage({
                                id: assistantId,
                                role: 'assistant',
                                content: evt.response,
                                products: evt.products,
                                timestamp: new Date(),
                            });
                        }
                    } else if (evt.type === 'error') {
                        setStreamingId(null);
                        appendMessage({
                            id: crypto.randomUUID(),
                            role: 'assistant',
                            content: `Sorry, something went wrong: ${evt.message}`,
                            timestamp: new Date(),
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            appendMessage({
                id: crypto.randomUUID(),
                role: 'assistant',
                content: 'Sorry, I could not reach the advisor. Please try again.',
                timestamp: new Date(),
            });
        } finally {
            setIsLoading(false);
            setStreamingId(null);
            inputRef.current?.focus();
        }
    };

    const uploadFile = async (file: File) => {
        appendMessage({
            id: crypto.randomUUID(),
            role: 'user',
            content: `Uploaded: ${file.name}`,
            timestamp: new Date(),
        });
        setIsLoading(true);
        setThinkingStage('Scanning your label...');

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (sessionId) formData.append('session_id', sessionId);

            setThinkingStage('Reading the supplement facts...');
            const response = await fetch(`${API_URL}/upload`, {
                method: 'POST',
                headers: { 'X-API-Key': API_KEY },
                body: formData,
            });

            const data = await response.json();

            if (!data.success) {
                appendMessage({
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: `I couldn't read that file: ${data.error}`,
                    timestamp: new Date(),
                });
                return;
            }

            if (!sessionId && data.session_id) setSessionId(data.session_id);

            const extracted = data.extracted as Record<string, string | null>;
            const lines = Object.entries(extracted)
                .filter(([k, v]) => v && !PROSE_FIELDS.has(k))
                .map(([k, v]) => {
                    const value = k === 'category'
                        ? (CATEGORY_META[v as string]?.label ?? titleCase(v as string))
                        : (k === 'product_name' || k === 'brand_or_make' || k === 'price')
                            ? v
                            : titleCase(v as string);
                    return `- **${EXTRACTED_LABELS[k] || k}:** ${value}`;
                });

            const scannedMessage = data.message || `Scanned successfully: ${file.name}`;
            const summary = `**${scannedMessage}**\nHere's what I found on your label:\n${lines.join('\n')}` +
                (data.alternatives?.length ? '\n\nHere are some catalog alternatives worth a look:' : '\n\nI could not find a close match in the catalog for that one.');

            appendMessage({
                id: crypto.randomUUID(),
                role: 'assistant',
                content: summary,
                products: data.alternatives,
                timestamp: new Date(),
            });
        } catch (error) {
            console.error('Upload error:', error);
            appendMessage({
                id: crypto.randomUUID(),
                role: 'assistant',
                content: 'Sorry, I could not analyze that file. Please try again.',
                timestamp: new Date(),
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        e.target.value = '';
        if (!file) return;
        if (file.type !== 'application/pdf') {
            appendMessage({
                id: crypto.randomUUID(),
                role: 'assistant',
                content: 'Please upload a PDF file.',
                timestamp: new Date(),
            });
            return;
        }
        uploadFile(file);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="flex h-full w-full flex-col overflow-hidden">
            {/* Header */}
            <header className="flex flex-shrink-0 items-center gap-3 border-b border-slate-200 bg-white/85 px-4 py-3 backdrop-blur sm:px-6">
                <div className="relative flex-shrink-0">
                    <BotAvatar size="lg" />
                    <span className="absolute -bottom-0.5 -right-0.5 block h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
                </div>
                <div className="min-w-0 flex-1">
                    <h1 className="truncate text-base font-semibold text-slate-900">
                        GymRAG &middot; Supplement Advisor
                    </h1>
                    <p className="truncate text-xs text-slate-500">
                        Online &middot; Ask about whey, creatine, pre-workout, recovery &amp; multivitamins
                    </p>
                </div>
                <button
                    type="button"
                    onClick={startNewChat}
                    disabled={isLoading || messages.length === 0}
                    aria-label="Start a new chat"
                    className="flex flex-shrink-0 items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-teal-400 hover:bg-teal-50 hover:text-teal-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                    <PlusCircle className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">New chat</span>
                </button>
            </header>

            {/* Messages */}
            <div
                ref={messagesContainerRef}
                className="scrollbar-thin flex-1 overflow-y-auto px-4 py-6 sm:px-6"
            >
                <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
                    {messages.length === 0 && (
                        <div className="flex flex-1 flex-col items-center justify-center px-4 py-10 text-center">
                            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-600 ring-1 ring-inset ring-teal-600/20">
                                <Dumbbell className="h-6 w-6" />
                            </div>
                            <p className="text-sm font-semibold text-slate-900">
                                Hi, I&apos;m your gym supplement advisor.
                            </p>
                            <p className="mt-1 max-w-xs text-sm text-slate-500">
                                Tell me your goal, a problem you&apos;re having, or upload a
                                supplement label &mdash; try one of these to get started.
                            </p>
                            <div className="mt-5 flex w-full max-w-sm flex-col gap-2">
                                {SUGGESTIONS.map((suggestion) => (
                                    <button
                                        key={suggestion}
                                        type="button"
                                        onClick={() =>
                                            suggestion.startsWith('Upload')
                                                ? fileInputRef.current?.click()
                                                : sendMessage(suggestion)
                                        }
                                        className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-left text-sm text-slate-700 shadow-sm transition-colors hover:border-teal-400 hover:bg-teal-50 hover:text-teal-800"
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`animate-message-in flex items-end gap-2.5 ${
                                message.role === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                        >
                            {message.role === 'assistant' && <BotAvatar />}

                            <div
                                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm sm:max-w-[80%] ${
                                    message.role === 'user'
                                        ? 'rounded-br-md bg-gradient-to-br from-teal-500 to-cyan-600 text-white'
                                        : 'rounded-bl-md border border-slate-200 bg-white text-slate-800'
                                }`}
                            >
                                {message.role === 'assistant' ? (
                                    <FormattedText text={message.content} />
                                ) : (
                                    <p className="whitespace-pre-wrap">{message.content}</p>
                                )}

                                {message.products && message.products.length > 0 && (
                                    <div className="mt-3 flex flex-col gap-2">
                                        {message.products.map((product, idx) => (
                                            <ProductCard key={idx} product={product} />
                                        ))}
                                    </div>
                                )}

                                <p
                                    className={`mt-1 text-[10px] ${
                                        message.role === 'user' ? 'text-teal-50/90' : 'text-slate-400'
                                    }`}
                                >
                                    {message.timestamp.toLocaleTimeString([], {
                                        hour: '2-digit',
                                        minute: '2-digit',
                                    })}
                                </p>
                            </div>

                            {message.role === 'user' && (
                                <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-slate-700 text-white">
                                    <User className="h-3.5 w-3.5" />
                                </div>
                            )}
                        </div>
                    ))}

                    {isLoading && !streamingId && <ThinkingIndicator stage={thinkingStage} />}
                </div>
            </div>

            {/* Input */}
            <div className="flex-shrink-0 border-t border-slate-200 bg-white px-4 py-3 sm:px-6">
                <div className="mx-auto w-full max-w-2xl">
                    <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1.5 pl-2 transition-colors focus-within:border-teal-400 focus-within:bg-white focus-within:ring-2 focus-within:ring-teal-500/20">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="application/pdf"
                            className="hidden"
                            onChange={handleFileSelected}
                        />
                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isLoading}
                            aria-label="Upload a supplement label PDF"
                            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-teal-50 hover:text-teal-600 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                            <Paperclip className="h-4 w-4" />
                        </button>
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyPress}
                            placeholder="Ask about supplements, or attach a label..."
                            maxLength={2000}
                            className="flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
                            disabled={isLoading}
                        />
                        <button
                            onClick={() => sendMessage()}
                            disabled={!input.trim() || isLoading}
                            aria-label="Send message"
                            className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 text-white shadow-sm transition-all hover:shadow-md disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
                        >
                            <Send className="h-4 w-4" />
                        </button>
                    </div>
                    <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-[11px] leading-snug text-slate-400">
                        <Info className="h-3 w-3 flex-shrink-0" />
                        AI-generated from our live catalog. Always retrieved, never invented.
                    </p>
                    <p className="mt-0.5 text-center text-[10px] text-slate-300">Built by RIZS</p>
                </div>
            </div>
        </div>
    );
}
