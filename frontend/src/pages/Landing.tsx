import {
  ExchangeShowcase,
  FeatureBento,
  Hero,
  HowItWorks,
  LandingFooter,
  MiniHeader,
  PricingTable,
  Ticker
} from "@/features/marketing"

export default function Landing() {
  return (
    <>
      <MiniHeader />
      <Ticker />
      <Hero />
      <ExchangeShowcase />
      <HowItWorks />
      <FeatureBento />
      <PricingTable />
      <LandingFooter />
    </>
  )
}
