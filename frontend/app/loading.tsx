/**
 * Loading Component
 * Displayed while page is loading
 */

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-secondary-500">
      <div className="text-center">
        {/* Logo */}
        <div className="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-2xl mb-8 mx-auto animate-float">
          <span className="text-white font-bold text-4xl">H</span>
        </div>

        {/* Loading Spinner */}
        <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4" />

        {/* Loading Text */}
        <p className="text-white text-lg font-medium">Loading HAVEN Token...</p>
      </div>
    </div>
  );
}
