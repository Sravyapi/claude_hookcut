import type { Variants, Transition } from "framer-motion";

/* ─── Shared spring configs ─── */
const spring: Transition = {
  type: "spring",
  stiffness: 200,
  damping: 24,
};

const springSnappy: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 25,
};

/* ─── Container that staggers children ─── */
export const staggerContainer: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1,
    },
  },
};

/* ─── Fade up child (for lists, grids) ─── */
export const fadeUpItem: Variants = {
  hidden: { opacity: 0, y: 20, filter: "blur(4px)" },
  show: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: spring,
  },
};

/* ─── Scale in (cards, modals) ─── */
export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  show: {
    opacity: 1,
    scale: 1,
    transition: springSnappy,
  },
};

/* ─── Slide right (step transitions) ─── */
export const slideRight: Variants = {
  hidden: { opacity: 0, x: 40 },
  show: {
    opacity: 1,
    x: 0,
    transition: spring,
  },
  exit: {
    opacity: 0,
    x: -40,
    transition: { duration: 0.2 },
  },
};

/* ─── Fade up (single element) ─── */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: {
    opacity: 1,
    y: 0,
    transition: spring,
  },
};
