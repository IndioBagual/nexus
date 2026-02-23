import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { X, Send, Bot, User, Activity, Link as LinkIcon, AlertCircle } from 'lucide-react';
import { cortexClient } from '../../lib/cortexClient';
import type { ChatMessage } from '../../lib/apiTypes';

interface CortexDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CortexDrawer({ isOpen, onClose }: CortexDrawerProps) {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Histórico da sessão em memória (MVP)
  const [messages, setMessages] = useState<ChatMessage[]>([{
    id: 'msg_welcome',
    role: 'cortex',
    content: 'Gateway Neural estabelecido. Como posso ajudar com a sua soberania hoje?',
    status: 'success'
  }]);

  // Auto-scroll para a última mensagem
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await cortexClient.chat(userMsg.content);
      
      const cortexMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'cortex',
        // Pega o "reply", se não tiver pega o "response", se for texto puro pega ele mesmo:
        content: res.reply || (res as any).response || (typeof res === 'string' ? res : 'Conexão estabelecida, mas o formato da resposta é desconhecido.'),
        status: res.status || 'success',
        // BLINDAGEM: Garante que sempre será um Array (lista)
        execution_report: Array.isArray(res.execution_report) ? res.execution_report : [],
        citations: Array.isArray(res.citations) ? res.citations : []
      };
      
      setMessages(prev => [...prev, cortexMsg]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'cortex',
        content: '**Erro Crítico:** Não foi possível contactar o Córtex. Verifique o servidor local.',
        status: 'success'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Navegação baseada no tipo de citação
  const handleCitationClick = (type: string, id: string) => {
    if (type === 'note') navigate(`/library?noteId=${id}`);
    if (type === 'task') navigate(`/chronos?taskId=${id}`);
    if (type === 'transaction') navigate(`/treasury?txId=${id}`);
    onClose(); // Fecha o drawer para o usuário ver a tela
  };

  return (
    <>
      {/* Overlay Escuro (Fecha ao clicar fora) */}
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-zinc-950/50 backdrop-blur-sm transition-opacity" onClick={onClose} />
      )}

      {/* Painel Lateral */}
      <div className={`fixed inset-y-0 right-0 z-50 w-full md:w-[450px] bg-zinc-950 border-l border-zinc-800 shadow-2xl transform transition-transform duration-300 ease-in-out flex flex-col ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        
        {/* Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center gap-2 text-zinc-100">
            <Bot className="w-5 h-5 text-emerald-500" />
            <span className="font-semibold tracking-wide">NEXUS Córtex</span>
          </div>
          <button onClick={onClose} className="p-2 text-zinc-400 hover:text-zinc-100 rounded-md hover:bg-zinc-800 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Chat Area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              
              {/* Balão de Mensagem */}
              <div className={`max-w-[85%] rounded-lg p-3 ${msg.role === 'user' ? 'bg-zinc-800 text-zinc-100' : 'bg-transparent text-zinc-300'}`}>
                {msg.role === 'user' ? (
                  <div className="text-sm">{msg.content}</div>
                ) : (
                  <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-zinc-900 prose-pre:border prose-pre:border-zinc-800">
                    {msg.status === 'needs_clarification' && (
                      <div className="flex items-center gap-2 text-amber-500 mb-2 font-medium">
                        <AlertCircle className="w-4 h-4" /> Pedido de Clarificação
                      </div>
                    )}
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              {/* Execution Report (Tools) */}
              {Array.isArray(msg.execution_report) && msg.execution_report.length > 0 && (
                <div className="mt-2 w-full max-w-[85%] bg-zinc-900/50 border border-zinc-800 rounded-md p-2 text-xs">
                  <div className="flex items-center gap-1.5 text-zinc-500 font-medium mb-1.5 uppercase tracking-wider">
                    <Activity className="w-3 h-3" /> Relatório de Execução
                  </div>
                  <ul className="space-y-1">
                    {msg.execution_report.map((item, i) => (
                      <li key={i} className="flex items-center justify-between p-1.5 bg-zinc-900 rounded">
                        <span className="text-zinc-400 font-mono">{item.tool}</span>
                        <span className={item.status === 'success' ? 'text-emerald-500' : 'text-red-500'}>
                          {item.details}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Citations (Referências ao Zettelkasten) */}
              {Array.isArray(msg.citations) && msg.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2 max-w-[85%]">
                  {msg.citations.map((cit, i) => (
                    <button 
                      key={i}
                      onClick={() => handleCitationClick(cit.type, cit.id)}
                      className="flex items-center gap-1.5 px-2 py-1 bg-zinc-800/50 hover:bg-zinc-700 text-zinc-400 hover:text-amber-400 border border-zinc-700/50 rounded text-[10px] transition-colors"
                    >
                      <LinkIcon className="w-3 h-3" /> {cit.title}
                    </button>
                  ))}
                </div>
              )}

            </div>
          ))}

          {/* Indicador de Carregamento */}
          {isLoading && (
            <div className="flex items-start gap-2 text-zinc-500 animate-pulse">
              <Bot className="w-4 h-4 mt-0.5" />
              <span className="text-sm">Processando intenção...</span>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-zinc-900/50 border-t border-zinc-800">
          <div className="relative flex items-center">
            <input 
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Envie um comando ou pergunte..."
              className="w-full bg-zinc-900 border border-zinc-700 focus:border-emerald-500 rounded-lg pl-4 pr-12 py-3 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all"
            />
            <button 
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="absolute right-2 p-1.5 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>
    </>
  );
}