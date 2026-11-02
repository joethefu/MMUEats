import SimplePage from "./SimplePage";

export const AboutPage = () => (
  <SimplePage title="About MMUEats">
    <p>MMUEats is a campus food delivery platform built for Multimedia University of Kenya, connecting
      students and staff with campus vendors, cafeterias, and approved nearby restaurants.</p>
  </SimplePage>
);

export const ContactPage = () => (
  <SimplePage title="Contact Us">
    <p>Reach the MMUEats team at support@mmueats.com or through the Help Center for order and account issues.</p>
  </SimplePage>
);

export const HelpPage = () => (
  <SimplePage title="Help Center">
    <p>Find answers about ordering, payments, tracking, and your account. Can't find what you need? Contact support.</p>
  </SimplePage>
);

export const TermsPage = () => (
  <SimplePage title="Terms and Conditions">
    <p>By using MMUEats you agree to our platform terms governing ordering, payments, cancellations, and account conduct.</p>
  </SimplePage>
);

export const PrivacyPage = () => (
  <SimplePage title="Privacy Policy">
    <p>MMUEats collects only the information needed to process orders, deliveries, and payments, and never sells your personal data.</p>
  </SimplePage>
);

export const NotFoundPage = () => (
  <div className="mx-auto flex max-w-md flex-col items-center px-4 py-32 text-center">
    <h1 className="text-4xl font-extrabold text-brand-600">404</h1>
    <p className="mt-2 text-slate-600">Page not found.</p>
  </div>
);
