import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  ArrowRight, 
  Database, 
  Brain, 
  BarChart3, 
  Shield,
  Zap,
  Globe,
  CheckCircle,
} from 'lucide-react';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Database,
      title: 'Multi-Tenant Architecture',
      description: 'Secure data isolation per user with dedicated FAISS indexes',
    },
    {
      icon: Brain,
      title: 'Advanced AI Analysis',
      description: 'RAG + GraphRAG hybrid intelligence with vision capabilities',
    },
    {
      icon: BarChart3,
      title: 'Real-Time Dashboards',
      description: 'Live analytics with interactive visualizations',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Bank-grade encryption and compliance standards',
    },
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Query responses in under 2 seconds',
    },
    {
      icon: Globe,
      title: 'Universal Format Support',
      description: 'PDF, Excel, CSV, Images, and 20+ file types',
    },
  ];

  return (
    <div className="min-h-screen bg-dark-bg overflow-x-hidden">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-8">
        {/* Background Effects */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-purple/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        </div>

        <div className="relative z-10 max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-full mb-8">
              <Sparkles className="w-4 h-4 text-primary-400" />
              <span className="text-sm text-primary-400 font-medium">Enterprise Edition</span>
            </div>
            
            <h1 className="text-7xl font-bold mb-6 leading-tight">
              <span className="text-white">AI Business Analyst</span>
              <br />
              <span className="text-gradient">That Thinks Like You</span>
            </h1>
            
            <p className="text-xl text-gray-400 mb-12 max-w-3xl mx-auto leading-relaxed">
              Transform your business data into actionable insights with advanced AI. 
              Multi-tenant, real-time analytics, and GraphRAG technology in one powerful platform.
            </p>

            <div className="flex items-center justify-center space-x-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/overview')}
                className="px-8 py-4 bg-gradient-to-r from-primary-500 to-accent-purple rounded-xl text-white font-semibold flex items-center space-x-2 shadow-lg hover:shadow-glow transition-all"
              >
                <span>Get Started Free</span>
                <ArrowRight className="w-5 h-5" />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 bg-dark-card border border-dark-border rounded-xl text-gray-200 font-semibold hover:bg-dark-hover transition-all"
              >
                Watch Demo
              </motion.button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 mt-20 max-w-3xl mx-auto">
              {[
                { value: '99.9%', label: 'Uptime SLA' },
                { value: '<2s', label: 'Query Speed' },
                { value: '1M+', label: 'Documents' },
              ].map((stat, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className="text-center"
                >
                  <div className="text-4xl font-bold text-gradient mb-2">{stat.value}</div>
                  <div className="text-sm text-gray-400">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-8 relative">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold text-white mb-4">
              Everything You Need to <span className="text-gradient">Succeed</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Built for enterprise scale with features that matter
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -5 }}
                className="glass-card p-6 hover:shadow-card-hover transition-all"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-primary-500/20 to-accent-purple/20 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 px-8 bg-dark-surface/50">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl font-bold text-white mb-4">
              Trusted by <span className="text-gradient">Industry Leaders</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                quote: "This platform transformed how we analyze customer data. ROI in 3 months!",
                author: "Sarah Johnson",
                role: "VP of Analytics, TechCorp",
                rating: 5,
              },
              {
                quote: "The AI insights are incredibly accurate. It's like having a data scientist on demand.",
                author: "Michael Chen",
                role: "CEO, DataFlow Inc",
                rating: 5,
              },
              {
                quote: "Multi-tenant architecture saved us months of development time. Brilliant!",
                author: "Emily Rodriguez",
                role: "CTO, CloudScale",
                rating: 5,
              },
            ].map((testimonial, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6"
              >
                <div className="flex space-x-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, j) => (
                    <CheckCircle key={j} className="w-5 h-5 text-accent-green" />
                  ))}
                </div>
                <p className="text-gray-300 mb-4 leading-relaxed">"{testimonial.quote}"</p>
                <div>
                  <div className="font-semibold text-white">{testimonial.author}</div>
                  <div className="text-sm text-gray-400">{testimonial.role}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-4xl mx-auto text-center glass-card p-12 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-accent-purple/10" />
          <div className="relative z-10">
            <h2 className="text-5xl font-bold text-white mb-4">
              Ready to Transform Your Business?
            </h2>
            <p className="text-xl text-gray-400 mb-8">
              Join thousands of companies making data-driven decisions
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => navigate('/overview')}
              className="px-10 py-5 bg-gradient-to-r from-primary-500 to-accent-purple rounded-xl text-white font-semibold text-lg flex items-center space-x-2 mx-auto shadow-lg hover:shadow-glow transition-all"
            >
              <span>Start Your Journey</span>
              <ArrowRight className="w-6 h-6" />
            </motion.button>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-8 border-t border-dark-border">
        <div className="max-w-6xl mx-auto text-center text-gray-400">
          <p>© 2025 AI Business Analyst Enterprise. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
