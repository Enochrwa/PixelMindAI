import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Receipt,
  FileText,
  CreditCard,
  User,
  ChevronDown,
  Zap,
  Image,
  Sparkles,
  BarChart3,
  Sprout,
  Smile,
  ScanText,
  Layers,
  IdCard,
  Wand2,
  Tag,
  ShoppingCart,
  Leaf,
  Clock,
  Scan,
} from 'lucide-react';
import { useState } from 'react';
import { clsx } from 'clsx';

interface NavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
}

interface NavGroup {
  label: string;
  icon: React.ReactNode;
  color: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'OCR & Documents',
    icon: <ScanText size={14} />,
    color: 'text-indigo-400',
    items: [
      { label: 'Receipt Scanner', to: '/tools/receipt-scanner', icon: <Receipt size={13} /> },
      { label: 'Invoice Reader', to: '/tools/invoice-reader', icon: <FileText size={13} /> },
      {
        label: 'Business Card Scanner',
        to: '/tools/business-card-scanner',
        icon: <CreditCard size={13} />,
      },
      { label: 'Handwriting OCR', to: '/tools/handwriting-ocr', icon: <Scan size={13} /> },
      { label: 'ID Card Reader', to: '/tools/id-card-reader', icon: <IdCard size={13} /> },
      { label: 'Document Scanner', to: '/tools/document-scanner', icon: <Layers size={13} /> },
      { label: 'Stamp Detector', to: '/tools/stamp-detector', icon: <Tag size={13} /> },
      { label: 'Table Extractor', to: '/tools/table-extractor', icon: <BarChart3 size={13} /> },
    ],
  },
  {
    label: 'Photo Intelligence',
    icon: <Image size={14} />,
    color: 'text-cyan-400',
    items: [
      { label: 'Background Remover', to: '/tools/background-remover', icon: <Image size={13} /> },
      { label: 'Deepfake Detector', to: '/tools/deepfake-detector', icon: <Scan size={13} /> },
      { label: 'Passport Photo', to: '/tools/passport-photo', icon: <IdCard size={13} /> },
      { label: 'Face Enhancer', to: '/tools/face-enhancer', icon: <Wand2 size={13} /> },
      { label: 'Object Detector', to: '/tools/object-detector', icon: <Layers size={13} /> },
      { label: 'Image Classifier', to: '/tools/image-classifier', icon: <Tag size={13} /> },
      { label: 'NSFW Detector', to: '/tools/nsfw-detector', icon: <Sparkles size={13} /> },
    ],
  },
  {
    label: 'Creator Studio',
    icon: <Sparkles size={14} />,
    color: 'text-violet-400',
    items: [
      {
        label: 'Thumbnail Analyzer',
        to: '/tools/thumbnail-analyzer',
        icon: <BarChart3 size={13} />,
      },
      { label: 'Caption Lens', to: '/tools/caption-lens', icon: <Sparkles size={13} /> },
      { label: 'Meme Generator Pro', to: '/tools/meme-generator', icon: <Smile size={13} /> },
      {
        label: 'Video Thumbnail Extractor',
        to: '/tools/video-thumbnail-extractor',
        icon: <Clock size={13} />,
      },
    ],
  },
  {
    label: 'Business Intel',
    icon: <BarChart3 size={14} />,
    color: 'text-amber-400',
    items: [
      { label: 'Shelf Counter', to: '/tools/shelf-counter', icon: <ShoppingCart size={13} /> },
      { label: 'Chart Reader', to: '/tools/chart-reader', icon: <BarChart3 size={13} /> },
      { label: 'Vehicle Plate OCR', to: '/tools/vehicle-plate-ocr', icon: <Scan size={13} /> },
      { label: 'Crowd Counter', to: '/tools/crowd-counter', icon: <Layers size={13} /> },
      { label: 'Safety Inspector', to: '/tools/safety-inspector', icon: <Sparkles size={13} /> },
      { label: 'Damage Assessor', to: '/tools/damage-assessor', icon: <Tag size={13} /> },
      {
        label: 'Signature Verifier',
        to: '/tools/signature-verifier',
        icon: <FileText size={13} />,
      },
      { label: 'Meter Reader', to: '/tools/meter-reader', icon: <ScanText size={13} /> },
    ],
  },
  {
    label: 'Agriculture AI',
    icon: <Sprout size={14} />,
    color: 'text-green-400',
    items: [
      {
        label: 'Plant Disease Detector',
        to: '/tools/plant-disease-detector',
        icon: <Leaf size={13} />,
      },
      {
        label: 'Crop Yield Estimator',
        to: '/tools/crop-yield-estimator',
        icon: <BarChart3 size={13} />,
      },
      { label: 'Soil Analyzer', to: '/tools/soil-analyzer', icon: <Layers size={13} /> },
      { label: 'Pest Identifier', to: '/tools/pest-identifier', icon: <Scan size={13} /> },
      { label: 'Weed Detector', to: '/tools/weed-detector', icon: <Tag size={13} /> },
      { label: 'Harvest Readiness', to: '/tools/harvest-readiness', icon: <Clock size={13} /> },
    ],
  },
  {
    label: 'Entertainment',
    icon: <Smile size={14} />,
    color: 'text-pink-400',
    items: [
      { label: 'Age Predictor', to: '/tools/age-predictor', icon: <Smile size={13} /> },
      { label: 'Celebrity Match', to: '/tools/celebrity-match', icon: <User size={13} /> },
      { label: 'Emotion Detector', to: '/tools/emotion-detector', icon: <Sparkles size={13} /> },
      { label: 'Art Style Analyzer', to: '/tools/art-style-analyzer', icon: <Wand2 size={13} /> },
      { label: 'Movie Scene ID', to: '/tools/movie-scene-id', icon: <Layers size={13} /> },
      { label: 'Food Identifier', to: '/tools/food-identifier', icon: <Tag size={13} /> },
      { label: 'Pet Breed ID', to: '/tools/pet-breed-id', icon: <Image size={13} /> },
    ],
  },
];

const TOP_LINKS: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: <LayoutDashboard size={14} /> },
];

const BOTTOM_LINKS: NavItem[] = [{ label: 'Account', to: '/account', icon: <User size={14} /> }];

function NavLinkItem({ to, icon, label }: NavItem) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs transition-colors',
          isActive
            ? 'bg-indigo-500/15 font-medium text-indigo-300'
            : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
        )
      }
    >
      <span className="shrink-0 opacity-70">{icon}</span>
      <span className="truncate">{label}</span>
    </NavLink>
  );
}

function NavGroupSection({ group }: { group: NavGroup }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500 transition-colors hover:bg-gray-800/50 hover:text-gray-300"
      >
        <span className={clsx('flex items-center gap-1.5', group.color)}>
          {group.icon}
          <span className="text-gray-400">{group.label}</span>
        </span>
        <ChevronDown
          size={11}
          className={clsx('text-gray-500 transition-transform', open ? 'rotate-0' : '-rotate-90')}
        />
      </button>
      {open && (
        <div className="mt-0.5 space-y-0.5 pb-1 pl-2">
          {group.items.map((item) => (
            <NavLinkItem key={item.to} {...item} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col border-r border-gray-800 bg-gray-900 px-2 py-4">
      {/* Logo */}
      <div className="mb-4 px-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600">
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-sm font-bold text-white">PixelMind AI</span>
        </div>
      </div>

      {/* Top nav */}
      <nav className="mb-2 space-y-0.5">
        {TOP_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-indigo-500/15 font-medium text-indigo-300'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              )
            }
          >
            <span className="shrink-0">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="mb-2 border-t border-gray-800" />

      {/* Tool groups — scrollable */}
      <nav className="scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent flex-1 space-y-0.5 overflow-y-auto pr-0.5">
        {NAV_GROUPS.map((group) => (
          <NavGroupSection key={group.label} group={group} />
        ))}
      </nav>

      <div className="mt-2 border-t border-gray-800 pt-2">
        {BOTTOM_LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-indigo-500/15 font-medium text-indigo-300'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              )
            }
          >
            <span className="shrink-0">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </div>
    </aside>
  );
}
