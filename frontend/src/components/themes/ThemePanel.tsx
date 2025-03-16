import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Theme, ThemeQuestion, ThemeTab } from '@/types/themes';
import { Compass, GitBranch, MessageCircle } from 'lucide-react';
import ThemeAskSection from './ThemeAskSection';

interface ThemePanelProps {
  theme: Theme;
  isOpen: boolean;
  selectedTab: ThemeTab;
  onClose: () => void;
  onTabChange: (tab: ThemeTab) => void;
  questions: ThemeQuestion[];
  onQuestionsChange: () => void;
}

export default function ThemePanel({
  theme,
  isOpen,
  selectedTab,
  onClose,
  onTabChange,
  questions,
  onQuestionsChange,
}: ThemePanelProps) {
  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-[900px] pl-8 pr-8">
        <SheetHeader className="flex flex-row items-center justify-between -ml-4">
          <SheetTitle className="text-xl">{theme.category}</SheetTitle>
        </SheetHeader>

        <Tabs
          value={selectedTab}
          onValueChange={(value) => onTabChange(value as ThemeTab)}
          className="mt-6"
        >
          <TabsList className="grid w-full grid-cols-3 rounded-none h-10 bg-[oklch(37.29%_0.0306_259.73)] p-0">
            <TabsTrigger 
              value="browse" 
              className="text-base rounded-none h-10 text-white data-[state=active]:bg-[oklch(71.48%_0.1257_215.22)] data-[state=active]:text-white hover:bg-[oklch(55.1%_0.0234_264.36)] data-[state=active]:shadow-none border-0"
            >
              <Compass className="h-4 w-4 mr-0.5" />
              Browse
            </TabsTrigger>
            <TabsTrigger 
              value="patterns" 
              className="text-base rounded-none h-10 text-white data-[state=active]:bg-[oklch(71.48%_0.1257_215.22)] data-[state=active]:text-white hover:bg-[oklch(55.1%_0.0234_264.36)] data-[state=active]:shadow-none border-0"
            >
              <GitBranch className="h-4 w-4 mr-0.5" />
              Patterns
            </TabsTrigger>
            <TabsTrigger 
              value="ask" 
              className="text-base rounded-none h-10 text-white data-[state=active]:bg-[oklch(71.48%_0.1257_215.22)] data-[state=active]:text-white hover:bg-[oklch(55.1%_0.0234_264.36)] data-[state=active]:shadow-none border-0"
            >
              <MessageCircle className="h-4 w-4 mr-0" />
              Ask
            </TabsTrigger>
          </TabsList>

          <TabsContent value="browse" className="mt-4">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Posts Summary</h3>
              <p className="text-slate-600">{theme.summary}</p>
              <Button>Browse all posts</Button>
            </div>
          </TabsContent>

          <TabsContent value="patterns" className="mt-4">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Common Patterns</h3>
              <p className="text-slate-600">
                Analysis of recurring topics and patterns in this theme...
              </p>
            </div>
          </TabsContent>

          <TabsContent value="ask" className="mt-4">
            <ThemeAskSection
              theme={theme}
              questions={questions}
              onQuestionsChange={onQuestionsChange}
            />
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
} 