import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  BookOpen,
  Lock,
  Mail,
  ChevronRight,
  User,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff,
} from "lucide-react";
import { z } from "zod";
import { loginSchema, forgotPasswordSchema, validateField } from "@/schemas/authSchemas";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { useAuth } from "@/hooks/useAuth";

import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { toast } from "@/components/ui/use-toast";

import { authApi } from "@/services/api/auth";

/**
 * Composant principal de connexion
 */
const Login = () => {
  // ---- État global d'authentification ----
  const { isAuthenticated, loading, error, login } = useAuth();
  // ---- État local du formulaire ----
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  // ---- État de validation ----
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [touched, setTouched] = useState({ email: false, password: false });

  // ---- État du dialogue "mot de passe oublié" ----
  const [forgotPasswordOpen, setForgotPasswordOpen] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState("");
  const [forgotPasswordEmailError, setForgotPasswordEmailError] = useState<string | null>(null);
  const [forgotPasswordStatus, setForgotPasswordStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  /* ----------------------------------------------------------------------- */
  /*                            Handlers                                     */
  /* ----------------------------------------------------------------------- */

  // ---- Handlers de validation en temps réel ----
  const handleEmailChange = (value: string) => {
    setEmail(value);
    
    // Validation en temps réel si le champ a été touché
    if (touched.email) {
      const error = validateField(loginSchema, 'email', value);
      setEmailError(error);
    }
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    
    // Validation en temps réel si le champ a été touché
    if (touched.password) {
      const error = validateField(loginSchema, 'password', value);
      setPasswordError(error);
    }
  };

  const handleEmailBlur = () => {
    setTouched(prev => ({ ...prev, email: true }));
    const error = validateField(loginSchema, 'email', email);
    setEmailError(error);
  };

  const handlePasswordBlur = () => {
    setTouched(prev => ({ ...prev, password: true }));
    const error = validateField(loginSchema, 'password', password);
    setPasswordError(error);
  };

  const handleForgotPasswordEmailChange = (value: string) => {
    setForgotPasswordEmail(value);
    
    // Validation en temps réel pour l'email du formulaire de réinitialisation
    const error = validateField(forgotPasswordSchema, 'email', value);
    setForgotPasswordEmailError(error);
  };
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // Validation complète avant soumission
    try {
      const validatedData = loginSchema.parse({ email, password, rememberMe });
      setEmailError(null);
      setPasswordError(null);
      
      await login({ 
        email: validatedData.email, 
        password: validatedData.password, 
        rememberMe: validatedData.rememberMe || false 
      });
    } catch (error) {
      if (error instanceof z.ZodError) {
        // Afficher les erreurs de validation
        const fieldErrors = error.flatten().fieldErrors;
        setEmailError(fieldErrors.email?.[0] || null);
        setPasswordError(fieldErrors.password?.[0] || null);
        return;
      }
    }
  };
  /** Réinitialisation du mot de passe */
  const handleForgotPassword = async (e: FormEvent) => {
    e.preventDefault();
    
    // Validation avant soumission
    try {
      const validatedData = forgotPasswordSchema.parse({ email: forgotPasswordEmail });
      setForgotPasswordEmailError(null);
      
      setForgotPasswordStatus("loading");
      setForgotPasswordEmail(forgotPasswordEmail.trim());

      const res = await authApi.requestPasswordReset({ email: forgotPasswordEmail });
      if (res.success) {
        setForgotPasswordStatus("success");
      } else {
        setForgotPasswordStatus("error");
      }
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        // Afficher les erreurs de validation
        const fieldErrors = error.flatten().fieldErrors;
        setForgotPasswordEmailError(fieldErrors.email?.[0] || null);
        return;
      }
      
      setForgotPasswordStatus("error");
      const errorMessage = error.response?.status === 404 
        ? "Aucun compte n'est associé à cette adresse email."
        : "Une erreur est survenue lors de la réinitialisation du mot de passe.";
      
      toast({
        title: "Erreur",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };
  const resetForgotPassword = () => {
    setForgotPasswordEmail("");
    setForgotPasswordEmailError(null);
    setForgotPasswordStatus("idle");
    setForgotPasswordOpen(false);
  };

  // Redirige l'utilisateur déjà connecté
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  /* ------------------------------------------------------------------------- */
  /*                             Rendu principal                               */
  /* ------------------------------------------------------------------------- */
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <div className="container mx-auto px-4 h-screen flex flex-col">
        {/* ----------------------------- Header ----------------------------- */}
        <header className="py-4 flex justify-between items-center">
            <img src="../logo.png" alt="Logo Edge Attendance System" className="h-10 w-25 rounded-full mx-auto" />
        </header>
        {/* ---------------------------- Main ------------------------------ */}
        <main className="flex-1 flex items-center justify-center">
          <div className="w-full sm:w-4/5 max-w-6xl flex flex-col md:flex-row rounded-xl shadow-lg overflow-hidden">
            {/* ----------- Colonne gauche : description ----------- */}
            <aside className="w-full md:w-1/2 bg-[#1f3d7a] text-white p-6 sm:p-8 md:p-12 flex flex-col justify-center">
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4">Edge Attendance System</h1>
              <p className="text-blue-100 text-sm sm:text-base mb-4 sm:mb-6">Gérez vos présences et suivez les activités des apprenants en temps réel.</p>

              <div className="grid grid-cols-1 gap-4 sm:gap-6 mt-3 sm:mt-4">
                {/* Bloc fonctionnel */}
                <Feature icon={<User className="w-5 h-4 sm:w-6 sm:h-5" />} title="Gestion des apprenants" desc="Suivez les présences et les activités des étudiants" />
                <Feature icon={<BookOpen className="w-5 h-4 sm:w-6 sm:h-5" />} title="Modules de présence" desc="Gérez les modules RFID et de reconnaissance faciale" />
                <Feature icon={<AlertCircle className="w-5 h-4 sm:w-6 sm:h-5" />} title="Alertes et notifications" desc="Soyez informé des événements importants" />
              </div>
            </aside>

            {/* ----------- Colonne droite : formulaire ----------- */}
            <section className="w-full md:w-1/2 bg-white p-5 sm:p-8 md:p-12 flex flex-col justify-center">
              {/* Titre */}
              <header className="mb-5 sm:mb-8">
                <h2 className="text-xl sm:text-2xl font-bold mb-1 sm:mb-2 text-[#1f3d7a]">Connexion</h2>
                <p className="text-gray-600 text-xs sm:text-sm">Identifiez-vous pour accéder à votre espace personnel</p>
              </header>

              {/* Formulaire */}
              <form onSubmit={handleSubmit} className="space-y-5">
                {/* Erreur globale */}
                {error && (
                  <Alert variant="destructive" aria-live="assertive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}                
                {/* Champ email */}               
                <FormField
                  id="email"
                  type="email"
                  label="Email"
                  value={email}
                  onChange={handleEmailChange}
                  onBlur={handleEmailBlur}
                  placeholder="Entrez votre email"
                  autoComplete="email"
                  icon={<Mail className="h-3 w-3 sm:h-4 sm:w-4" />}
                  error={emailError}
                />                
                {/* Champ mot de passe */}
                <FormField
                  id="password"
                  type={showPassword ? "text" : "password"}
                  label="Mot de passe"
                  value={password}
                  onChange={handlePasswordChange}
                  onBlur={handlePasswordBlur}
                  placeholder="Entrez votre mot de passe"
                  autoComplete="current-password"
                  icon={<Lock className="h-3 w-3 sm:h-4 sm:w-4" />}
                  error={passwordError}
                >
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-2 h-6 w-6 text-gray-500 hover:text-gray-700 z-10"
                    onClick={() => setShowPassword(!showPassword)}
                    title={showPassword ? "Cacher le mot de passe" : "Afficher le mot de passe"}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </FormField>
                {/* Options sous le champ */}
                <div className="flex items-center justify-between mt-1.5 sm:mt-2">
                  {/* Checkbox "Se souvenir" */}
                  <label htmlFor="remember" className="flex items-center text-xs sm:text-sm text-gray-600">
                    <input
                      id="remember"
                      type="checkbox"
                      className="h-3 w-3 sm:h-4 sm:w-4 rounded border-gray-300 text-[#1f3d7a] focus:ring-[#1f3d7a]"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                    />
                    <span className="ml-1.5 sm:ml-2">Se souvenir de moi</span>
                  </label>

                  {/* Lien mot de passe oublié */}
                  <button
                    type="button"
                    onClick={() => setForgotPasswordOpen(true)}
                    className="text-xs sm:text-sm text-[#1f3d7a] hover:underline"
                  >
                    Mot de passe oublié&nbsp;?
                  </button>
                </div>
                {/* Bouton */}
                <Button
                  type="submit"
                  className="w-full h-9 sm:h-10 text-xs sm:text-sm bg-[#1f3d7a] hover:bg-[#2a4f94] transition-colors flex items-center justify-center"
                  disabled={loading || !!emailError || !!passwordError || !email || !password}
                >
                  {loading ? (
                    "Connexion en cours…"
                  ) : (
                    <>
                      Connexion
                      <ChevronRight className="ml-1 h-3 w-3 sm:h-4 sm:w-4" />
                    </>
                  )}
                </Button>
              </form>

              {/* Footer */}
              <footer className="mt-5 sm:mt-8 pt-4 sm:pt-6 border-t border-gray-200 text-center">
                <p className="text-xs sm:text-sm text-gray-600">Centre de Recherche d'Étude et de Créativité (CREC), Bénin</p>
                <p className="text-xs text-gray-500 mt-0.5 sm:mt-1">Système de gestion de présence des étudiants</p>
              </footer>
            </section>
          </div>
        </main>
      </div>

      {/* Dialog "mot de passe oublié" */}
      <Dialog open={forgotPasswordOpen} onOpenChange={setForgotPasswordOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Réinitialisation du mot de passe</DialogTitle>
            <DialogDescription>
              Entrez votre adresse email pour recevoir un nouveau mot de passe.
            </DialogDescription>
          </DialogHeader>

          {/* Succès */}
          {forgotPasswordStatus === "success" ? (
            <PasswordResetSuccess email={forgotPasswordEmail} onClose={resetForgotPassword} />
          ) : (
            /* Formulaire */            
            <form onSubmit={handleForgotPassword} className="space-y-4 py-4">              <FormField
                id="forgot-email"
                type="email"
                label="Adresse email"
                value={forgotPasswordEmail}
                onChange={handleForgotPasswordEmailChange}
                placeholder="exemple@crec-sj.bj"
                icon={<Mail className="h-3 w-3 sm:h-4 sm:w-4" />}
                error={forgotPasswordEmailError}
              />

              {/* Erreur */}
              {forgotPasswordStatus === "error" && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Aucun compte n'est associé à cette adresse email.
                  </AlertDescription>
                </Alert>
              )}

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setForgotPasswordOpen(false)}>
                  Annuler
                </Button>                
                <Button
                  type="submit"
                  disabled={forgotPasswordStatus === "loading" || !!forgotPasswordEmailError || !forgotPasswordEmail}
                  className="bg-[#1f3d7a] hover:bg-[#2a4f94]"
                >
                  {forgotPasswordStatus === "loading" ? "Envoi en cours…" : "Envoyer"}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Login;

/* =============================================================================
 * Sous‑composants utilitaires
 * ========================================================================= */

/**
 * Bloc descriptif dans la colonne gauche
 */
interface FeatureProps {
  icon: React.ReactNode;
  title: string;
  desc: string;
}

const Feature = ({ icon, title, desc }: FeatureProps) => (
  <div className="flex items-start">
    <div className="bg-blue-600 rounded-full p-1.5 sm:p-2 mr-3 sm:mr-4">{icon}</div>
    <div>
      <h3 className="text-lg sm:text-xl font-semibold">{title}</h3>
      <p className="text-blue-100 text-xs sm:text-sm mt-0.5 sm:mt-1">{desc}</p>
    </div>
  </div>
);

/**
 * Champ de formulaire stylisé
 */
interface FormFieldProps {
  id: string;
  type: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  placeholder?: string;
  icon?: React.ReactNode;
  children?: React.ReactNode;
  autoComplete?: string;
  error?: string | null;
}
const FormField = ({
  id,
  type,
  label,
  value,
  onChange,
  onBlur,
  placeholder,
  icon,
  children,
  autoComplete,
  error,
}: FormFieldProps) => (
  <div className="space-y-1.5 sm:space-y-2">
    <label htmlFor={id} className="block text-xs sm:text-sm font-medium text-gray-700">
      {label}
    </label>    
    <div className="relative">
      <div className="absolute left-3 top-[7px] sm:top-3 text-gray-400">
        {icon}
      </div>
      <Input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        placeholder={placeholder}
        className={`h-8 sm:h-10 pl-10 text-xs sm:text-sm ${id === 'password' ? 'pr-10' : ''} ${
          error ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
        }`}
        autoComplete={autoComplete}
        required
      />
      {children}
    </div>
    {error && (
      <p className="text-xs sm:text-sm text-red-600 flex items-center gap-1">
        <AlertCircle className="h-3 w-3 sm:h-4 sm:w-4" />
        {error}
      </p>
    )}
  </div>
);

/**
 * Affiche l'écran de succès après la demande de réinitialisation
 */
const PasswordResetSuccess = ({
  email,
  onClose,
}: {
  email: string;
  onClose: () => void;
}) => (
  <div className="py-6">
    <div className="flex flex-col items-center text-center gap-2">
      <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
        <CheckCircle className="h-6 w-6 text-green-600" />
      </div>
      <h3 className="font-medium text-lg">Email envoyé !</h3>
      <p className="text-gray-500 text-sm">
        Si un compte existe avec l'adresse <span className="font-medium">{email}</span>, vous recevrez un email
        avec les instructions pour réinitialiser votre mot de passe.
      </p>
    </div>
    <DialogFooter className="mt-6">
      <Button onClick={onClose}>Fermer</Button>
    </DialogFooter>
  </div>
);