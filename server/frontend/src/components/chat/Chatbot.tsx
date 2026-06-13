import { useState, useRef, useEffect } from "react";
import { X, MessageSquare, Send, Loader2, Bot, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar } from "@/components/ui/avatar";
import { ChatMessage } from "@/types";
import { cn } from "@/lib/utils";
import { chatService, ChatResponse } from "@/services/chatService";
import { useToast } from "@/hooks/use-toast";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      content: "Bonjour ! Je suis votre assistant IA administratif pour Edge Attendance System. Je peux vous aider à questions les données sur la plateforme. Comment puis-je vous aider ?",
      isUser: false,
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isServiceHealthy, setIsServiceHealthy] = useState(true);
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null);
  const [displayedText, setDisplayedText] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  // Effet de frappe pour les messages du bot
  useEffect(() => {
    if (typingMessageId) {
      const targetMessage = messages.find(msg => msg.id === typingMessageId && !msg.isUser);
      if (targetMessage && displayedText.length < targetMessage.content.length) {
        const timer = setTimeout(() => {
          setDisplayedText(targetMessage.content.slice(0, displayedText.length + 1));
        }, 3); // Vitesse de frappe (3ms par caractère)

        return () => clearTimeout(timer);
      } else if (targetMessage && displayedText.length >= targetMessage.content.length) {
        // Fin de l'effet de frappe
        setTypingMessageId(null);
        setDisplayedText("");
      }
    }
  }, [typingMessageId, displayedText, messages]);

  // Vérifier la santé du service au premier chargement
  useEffect(() => {
    if (isOpen) {
      checkServiceHealth();
    }
  }, [isOpen]);

  const checkServiceHealth = async () => {
    try {
      const health = await chatService.getHealthStatus();
      setIsServiceHealthy(health.status === "healthy");
      
      if (health.status === "unhealthy") {
        toast({
          title: "Service chatbot indisponible",
          description: "Le service IA rencontre des difficultés. Certaines fonctionnalités peuvent être limitées.",
          variant: "destructive"
        });
      }
    } catch (error) {
      setIsServiceHealthy(false);
      console.error("Erreur lors de la vérification de santé:", error);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (!message.trim() || isTyping) return;
    
    // Validation côté client
    if (message.length > 2000) {
      toast({
        title: "Message trop long",
        description: "Votre message ne peut pas dépasser 2000 caractères.",
        variant: "destructive"
      });
      return;
    }
    
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    const currentMessage = message;
    setMessage("");
    setIsTyping(true);
      try {
      // Appeler l'API 
      const response: ChatResponse = await chatService.sendMessage(currentMessage);
      
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: response.message,
        isUser: false,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, botMsg]);
      
      // Démarrer l'effet de frappe pour le nouveau message
      setTypingMessageId(botMsg.id);
      setDisplayedText("");
      
    } catch (error: any) {
      console.error("Erreur lors de l'envoi du message:", error);
      
      // Message d'erreur pour l'utilisateur
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: `❌ ${error.message || "Erreur lors du traitement de votre demande. Veuillez réessayer."}`,
        isUser: false,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMsg]);
      
      toast({
        title: "Erreur de chat",
        description: error.message || "Impossible de traiter votre demande",
        variant: "destructive"
      });
    } finally {
      setIsTyping(false);
    }
  };


  return (
    <>
      {/* Chatbot Button */}
      <button
        className={cn(
          "fixed bottom-6 right-6 w-14 h-14 rounded-full flex items-center justify-center text-white z-50 shadow-lg transition-all duration-300",
          "bg-[#1f3d7a] hover:bg-[#1f3d7a]/90",
          isOpen && "scale-0 opacity-0"
        )}
        onClick={() => setIsOpen(true)}
        aria-label="Ouvrir le chatbot"
      >
        <MessageSquare className="h-6 w-6" />
      </button>

      {/* Chatbot Modal */}
      <div
        className={cn(
          "fixed bottom-6 right-6 w-80 sm:w-96 h-[500px] max-h-[80vh] bg-white rounded-lg shadow-xl z-50",
          "flex flex-col overflow-hidden border border-gray-200",
          "transition-all duration-300 transform",
          isOpen ? "scale-100 opacity-100" : "scale-0 opacity-0"
        )}
      >        
      {/* Header */}
        <div className="bg-[#1f3d7a] text-white p-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5" />
            <div className="flex items-center space-x-2">
              <h3 className="font-medium">Assistant IA Edge Attendance System</h3>
              {!isServiceHealthy && (
                <span title="Service partiellement indisponible">
                  <AlertCircle className="h-4 w-4 text-yellow-300" />
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full text-white hover:bg-white/10"
              onClick={() => setIsOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
          <div className="space-y-4">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={cn(
                  "flex",
                  msg.isUser ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] rounded-lg px-4 py-2",
                    msg.isUser 
                      ? "bg-[#1f3d7a] text-white rounded-br-none" 
                      : "bg-white border border-gray-200 rounded-bl-none"
                  )}
                >
                  {!msg.isUser && (
                    <div className="flex items-center space-x-2 mb-1">
                      <Avatar className="h-6 w-6 bg-blue-100">
                        <Bot className="h-4 w-4 text-blue-600" />
                      </Avatar>
                      <span className="text-xs font-medium">Assistant</span>
                    </div>
                  )}
                  {msg.isUser ? (
                    <p className="text-sm whitespace-pre-wrap">
                      {msg.content}
                    </p>
                  ) : (
                    <div className="chatbot-markdown">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          // Personnalisation pour préserver l'effet de frappe
                          h1: ({children}) => <h1>{children}</h1>,
                          h2: ({children}) => <h2>{children}</h2>,
                          h3: ({children}) => <h3>{children}</h3>,
                          p: ({children}) => <p>{children}</p>,
                          ul: ({children}) => <ul>{children}</ul>,
                          ol: ({children}) => <ol>{children}</ol>,
                          li: ({children}) => <li>{children}</li>,
                          strong: ({children}) => <strong>{children}</strong>,
                          em: ({children}) => <em>{children}</em>,
                          code: ({children}) => <code>{children}</code>,
                          pre: ({children}) => <pre>{children}</pre>,
                          blockquote: ({children}) => <blockquote>{children}</blockquote>,
                          table: ({children}) => <table>{children}</table>,
                          th: ({children}) => <th>{children}</th>,
                          td: ({children}) => <td>{children}</td>,
                          hr: () => <hr />,
                          a: ({children, href}) => <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>,
                        }}
                      >
                        {typingMessageId === msg.id 
                          ? displayedText + (displayedText.length < msg.content.length ? '|' : '')
                          : msg.content
                        }
                      </ReactMarkdown>
                    </div>
                  )}
                  <div className="mt-1 text-right">
                    <span className={cn(
                      "text-xs",
                      msg.isUser ? "text-blue-100" : "text-gray-400"
                    )}>
                      {(typeof msg.timestamp === 'string' ? new Date(msg.timestamp) : msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </span>
                    {!msg.isUser && msg.contextUsed && msg.contextUsed > 0 && (
                      <span className="text-xs text-gray-400 ml-2">
                        • {msg.contextUsed} ctx • {msg.responseTime}ms
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg px-4 py-2 bg-white border border-gray-200 rounded-bl-none">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                    <span className="text-sm text-gray-500">Assistant écrit...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center space-x-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tapez votre message..."
              className="flex-1"
            />
            <Button 
              type="submit" 
              size="icon"
              className="h-10 w-10 rounded-full bg-[#1f3d7a] hover:bg-[#2a4f94]"
              disabled={!message.trim() || isTyping}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </>
  );
};

export default Chatbot;
