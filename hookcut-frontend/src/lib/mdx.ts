import fs from "fs";
import path from "path";
import matter from "gray-matter";

export interface PostFrontmatter {
  title: string;
  description: string;
  date: string;
  slug: string;
  keywords?: string[];
  author?: string;
  readingTime?: string;
  // Case study extras
  creator?: string;
  subscribers?: string;
  result?: string;
  niche?: string;
}

export interface Post {
  frontmatter: PostFrontmatter;
  content: string;
  slug: string;
}

function getContentDir(type: "blog" | "case-studies"): string {
  return path.join(process.cwd(), "src", "content", type);
}

export function getAllPosts(type: "blog" | "case-studies"): PostFrontmatter[] {
  const dir = getContentDir(type);
  if (!fs.existsSync(dir)) return [];

  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".mdx"));

  return files
    .map((filename) => {
      const raw = fs.readFileSync(path.join(dir, filename), "utf-8");
      const { data } = matter(raw);
      const slug = filename.replace(/\.mdx$/, "");
      return { ...(data as Omit<PostFrontmatter, "slug">), slug } as PostFrontmatter;
    })
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
}

export function getPost(type: "blog" | "case-studies", slug: string): Post | null {
  const dir = getContentDir(type);
  const filePath = path.join(dir, `${slug}.mdx`);

  if (!fs.existsSync(filePath)) return null;

  const raw = fs.readFileSync(filePath, "utf-8");
  const { data, content } = matter(raw);

  return {
    frontmatter: { ...(data as Omit<PostFrontmatter, "slug">), slug } as PostFrontmatter,
    content,
    slug,
  };
}

export function getAllSlugs(type: "blog" | "case-studies"): string[] {
  const dir = getContentDir(type);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".mdx"))
    .map((f) => f.replace(/\.mdx$/, ""));
}
