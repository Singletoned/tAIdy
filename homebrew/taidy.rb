class Taidy < Formula
  desc "Smart linter/formatter with automatic tool detection"
  homepage "https://github.com/singletoned/taidy"
  version "1.0.0"
  
  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/singletoned/taidy/releases/download/v#{version}/taidy-v#{version}-darwin-arm64.tar.gz"
      sha256 "REPLACE_WITH_ACTUAL_SHA256_ARM64"
    else
      url "https://github.com/singletoned/taidy/releases/download/v#{version}/taidy-v#{version}-darwin-amd64.tar.gz"  
      sha256 "REPLACE_WITH_ACTUAL_SHA256_AMD64"
    end
  end

  on_linux do
    if Hardware::CPU.arm?
      url "https://github.com/singletoned/taidy/releases/download/v#{version}/taidy-v#{version}-linux-arm64.tar.gz"
      sha256 "REPLACE_WITH_ACTUAL_SHA256_LINUX_ARM64"
    else
      url "https://github.com/singletoned/taidy/releases/download/v#{version}/taidy-v#{version}-linux-amd64.tar.gz"
      sha256 "REPLACE_WITH_ACTUAL_SHA256_LINUX_AMD64"
    end
  end

  def install
    bin.install Dir["taidy*"].first => "taidy"
  end

  test do
    system "#{bin}/taidy", "--version"
    system "#{bin}/taidy", "--help"
  end
end