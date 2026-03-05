import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { MDXRemote } from "next-mdx-remote/rsc";
import { getPost, getAllSlugs } from "@/lib/mdx";
import { BlogLayout } from "@/components/blog-layout";

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  return getAllSlugs("blog").map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = getPost("blog", slug);
  if (!post) return { title: "Not Found" };

  const { frontmatter } = post;
  return {
    title: `${frontmatter.title} | HookCut Blog`,
    description: frontmatter.description,
    keywords: frontmatter.keywords,
    openGraph: {
      title: frontmatter.title,
      description: frontmatter.description,
      type: "article",
      url: `https://hookcut.ai/blog/${slug}`,
      publishedTime: frontmatter.date,
    },
    twitter: { card: "summary_large_image", title: frontmatter.title, description: frontmatter.description },
    alternates: { canonical: `https://hookcut.ai/blog/${slug}` },
  };
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  const post = getPost("blog", slug);
  if (!post) notFound();

  const { frontmatter, content } = post;

  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: frontmatter.title,
    description: frontmatter.description,
    datePublished: frontmatter.date,
    author: { "@type": "Organization", name: "HookCut" },
    publisher: { "@type": "Organization", name: "HookCut", url: "https://hookcut.ai" },
    mainEntityOfPage: { "@type": "WebPage", "@id": `https://hookcut.ai/blog/${slug}` },
    keywords: frontmatter.keywords?.join(", "),
  };

  const breadcrumbJsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://hookcut.ai" },
      { "@type": "ListItem", position: 2, name: "Blog", item: "https://hookcut.ai/blog" },
      { "@type": "ListItem", position: 3, name: frontmatter.title, item: `https://hookcut.ai/blog/${slug}` },
    ],
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJsonLd) }} />
      <BlogLayout frontmatter={frontmatter} type="blog">
        <MDXRemote source={content} />
      </BlogLayout>
    </>
  );
}
