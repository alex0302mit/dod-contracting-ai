import { Upload, FileSearch, GitBranch, FileText } from "lucide-react";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface StrategyBoardProps {
  onStart: () => void;
  onAssumptions: () => void;
  onTrace: () => void;
  onPlan: () => void;
}

export function StrategyBoard({ onStart, onAssumptions, onTrace, onPlan }: StrategyBoardProps) {
  return (
    <div className="container mx-auto p-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent mb-3">
          Strategy Board
        </h1>
        <p className="text-lg text-muted-foreground">
          Your mission control for AI-powered acquisition document generation
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <ProcessCard
          icon={<Upload className="h-8 w-8" />}
          title="1. Uploads"
          description="Strategy + Requirements"
          onClick={onStart}
          gradient="from-blue-500 to-cyan-500"
        />
        <ProcessCard
          icon={<FileSearch className="h-8 w-8" />}
          title="2. Assumptions"
          description="Extract & curate"
          onClick={onAssumptions}
          gradient="from-purple-500 to-pink-500"
        />
        <ProcessCard
          icon={<GitBranch className="h-8 w-8" />}
          title="3. Traceability"
          description="Map requirements"
          onClick={onTrace}
          gradient="from-orange-500 to-red-500"
        />
        <ProcessCard
          icon={<FileText className="h-8 w-8" />}
          title="4. Generate"
          description="Draft documents"
          onClick={onPlan}
          gradient="from-green-500 to-emerald-500"
        />
      </div>
    </div>
  );
}

function ProcessCard({ icon, title, description, onClick, gradient }: any) {
  return (
    <Card
      className="cursor-pointer hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-2 hover:border-primary group"
      onClick={onClick}
    >
      <CardHeader>
        <div className={`h-16 w-16 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform shadow-lg`}>
          {icon}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription className="text-base">{description}</CardDescription>
      </CardHeader>
    </Card>
  );
}
