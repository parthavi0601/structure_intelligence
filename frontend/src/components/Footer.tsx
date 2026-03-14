import React from 'react';
import { Github, Twitter, Linkedin, Mail } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-neon-border/50 bg-neon-dark py-12 px-6">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="col-span-1 md:col-span-2">
          <h3 className="text-xl font-bold text-white tracking-widest uppercase mb-4">AI Structural Monitoring</h3>
          <p className="text-gray-400 text-sm max-w-sm">
            AI-powered monitoring, predictive maintenance, and digital twin simulation for bridges and critical infrastructure.
          </p>
        </div>
        
        <div>
          <h4 className="text-white font-semibold mb-4">Resources</h4>
          <ul className="space-y-2 text-sm text-gray-400">
            <li><a href="#" className="hover:text-neon-cyan transition-colors">Documentation</a></li>
            <li><a href="#" className="hover:text-neon-cyan transition-colors">API Reference</a></li>
            <li><a href="#" className="hover:text-neon-cyan transition-colors">Case Studies</a></li>
          </ul>
        </div>

        <div>
          <h4 className="text-white font-semibold mb-4">Connect</h4>
          <div className="flex gap-4 mb-4">
            <a href="#" className="text-gray-400 hover:text-neon-cyan transition-colors"><Github className="w-5 h-5" /></a>
            <a href="#" className="text-gray-400 hover:text-neon-cyan transition-colors"><Twitter className="w-5 h-5" /></a>
            <a href="#" className="text-gray-400 hover:text-neon-cyan transition-colors"><Linkedin className="w-5 h-5" /></a>
            <a href="#" className="text-gray-400 hover:text-neon-cyan transition-colors"><Mail className="w-5 h-5" /></a>
          </div>
          <ul className="space-y-2 text-sm text-gray-400 flex flex-wrap gap-x-4">
            <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
            <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
          </ul>
        </div>
      </div>
      <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-white/10 text-center text-sm text-gray-500">
        &copy; 2026 AI Structural Monitoring Platform. All rights reserved.
      </div>
    </footer>
  );
}
