import { Suspense } from "react";
import HomeStateMachine from "@/components/home-state-machine";
import { MarketingHome } from "@/components/marketing-home";
import { Footer } from "@/components/footer";

export default function Page() {
  return (
    <Suspense>
      <HomeStateMachine
        marketingContent={
          <>
            <main id="main-content">
              <MarketingHome />
            </main>
            <Footer />
          </>
        }
      />
    </Suspense>
  );
}
