import React from 'react';
import { motion } from 'framer-motion';
import { useUserStore } from '@/store/userStore';

interface BentoCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  colSpan?: number;
  rowSpan?: number;
  children?: React.ReactNode;
  className?: string;
  delay?: number;
}

export const BentoCard: React.FC<BentoCardProps> = ({
  title,
  description,
  icon,
  colSpan = 1,
  rowSpan = 1,
  children,
  className = '',
  delay = 0,
}) => {
  const { isDark } = useUserStore();
  const bg = isDark ? 'bg-white/5 border-white/10' : 'bg-gray-50 border-gray-200';
  const hoverBg = isDark ? 'hover:bg-white/10' : 'hover:bg-gray-100';
  const textTitle = isDark ? 'text-gray-100' : 'text-gray-900';
  const textDesc = isDark ? 'text-gray-400' : 'text-gray-600';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay }}
      className={`relative overflow-hidden rounded-3xl border p-6 flex flex-col gap-4 backdrop-blur-sm transition-all duration-300 ${bg} ${hoverBg} ${className}`}
      style={{
        gridColumn: `span ${colSpan}`,
        gridRow: `span ${rowSpan}`,
      }}
    >
      <div className="flex items-center gap-3">
        <div className={`p-3 rounded-2xl ${isDark ? 'bg-white/10' : 'bg-white shadow-sm border border-gray-100'}`}>
          {icon}
        </div>
        <h3 className={`text-xl font-bold ${textTitle}`}>{title}</h3>
      </div>
      <p className={`text-sm ${textDesc}`}>{description}</p>
      
      <div className="flex-1 mt-4 relative">
        {children}
      </div>
    </motion.div>
  );
};

interface BentoGridProps {
  children: React.ReactNode;
}

export const BentoGrid: React.FC<BentoGridProps> = ({ children }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 auto-rows-[250px]">
      {children}
    </div>
  );
};
