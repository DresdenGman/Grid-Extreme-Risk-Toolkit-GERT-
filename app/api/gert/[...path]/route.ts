import { handleGertRequest } from '@/lib/server/gert';

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function route(request: Request, context: RouteContext) {
  const { path } = await context.params;
  return handleGertRequest(request, path);
}

export const GET = route;
export const POST = route;
export const OPTIONS = route;
